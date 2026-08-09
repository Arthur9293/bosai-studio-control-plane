from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from .audit import AuditEvent, AuditTrail
from .authority import AuthorityExecutor, POLICY_VERSION
from .contracts import (
    AuthorityDecision,
    AuthorityGrant,
    Decision,
    ExecutionReceipt,
    Proposal,
)
from .durable_store import (
    AuthorityStateStore,
    DurablePermitRecord,
    DurablePermitState,
)
from .pipeline import MediaPipelineSim


class DurableAuditTrail(AuditTrail):
    """AuditTrail facade whose chain head and events are owned by the durable store."""

    def __init__(self, store: AuthorityStateStore) -> None:
        self.store = store

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return self.store.list_audit_events()

    def append(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        return self.store.append_audit(event_type, payload)

    def verify(self) -> bool:
        return self.store.verify_audit()


class PersistentAuthorityExecutor(AuthorityExecutor):
    """BOSAI authority executor with durable permit and audit state.

    The critical ordering is intentional:

    1. durable store atomically transitions an eligible permit to CONSUMED_PENDING;
    2. only after that transaction commits may the pipeline side effect run;
    3. terminal execution state is persisted afterwards.

    No external side effect is performed from a Firestore transaction callback.
    """

    def __init__(
        self,
        pipeline: MediaPipelineSim,
        *,
        grant: AuthorityGrant,
        store: AuthorityStateStore,
        permit_ttl: timedelta = timedelta(minutes=2),
    ) -> None:
        super().__init__(pipeline, grant=grant, permit_ttl=permit_ttl)
        self.store = store
        self.audit = DurableAuditTrail(store)

    def permit_state(self, permit_id: str) -> DurablePermitState | None:
        permit = self.store.get_permit(permit_id)
        return permit.status if permit else None

    def _persistent_deny(
        self,
        proposal: Proposal,
        reason_code: str,
        *,
        now: datetime,
        violated_invariant: str | None = None,
    ) -> AuthorityDecision:
        decision = AuthorityDecision(
            decision=Decision.DENIED,
            proposal_id=proposal.proposal_id,
            reason_code=reason_code,
            policy_version=POLICY_VERSION,
            violated_invariant=violated_invariant,
        )
        self.store.persist_decision(proposal, decision, created_at=now)
        self.audit.append("AUTHORITY_DENIED", decision.__dict__)
        return decision

    def evaluate(self, proposal: Proposal, *, now: datetime | None = None) -> AuthorityDecision:
        current_time = self._now(now)
        state = self.pipeline.snapshot()

        self.store.persist_policy(self.grant)
        self.store.persist_incident(state)
        self.store.persist_proposal(proposal, created_at=current_time)

        if self.grant.policy_version != POLICY_VERSION:
            return self._persistent_deny(
                proposal,
                "GRANT_POLICY_VERSION_MISMATCH",
                now=current_time,
            )
        if current_time >= self.grant.expires_at:
            return self._persistent_deny(
                proposal,
                "AUTHORITY_GRANT_EXPIRED",
                now=current_time,
            )
        if proposal.action not in self.grant.allowed_actions:
            return self._persistent_deny(
                proposal,
                "ACTION_OUTSIDE_AUTHORITY_GRANT",
                now=current_time,
            )
        if proposal.incident_id != state.incident_id:
            return self._persistent_deny(
                proposal,
                "INCIDENT_SCOPE_MISMATCH",
                now=current_time,
            )

        local_error = self._check_local_predicates(proposal, state)
        if local_error:
            return self._persistent_deny(
                proposal,
                local_error,
                now=current_time,
            )

        violated = self._check_global_invariants(proposal, state)
        if violated:
            return self._persistent_deny(
                proposal,
                "GLOBAL_TRAJECTORY_INVARIANT_VIOLATION",
                now=current_time,
                violated_invariant=violated,
            )

        permit_id = f"permit-{uuid4().hex[:16]}"
        permit = DurablePermitRecord(
            permit_id=permit_id,
            proposal_id=proposal.proposal_id,
            incident_id=proposal.incident_id,
            action=proposal.action,
            target=proposal.target,
            policy_version=POLICY_VERSION,
            bound_state_version=state.state_version,
            expires_at=current_time + self.permit_ttl,
            status=DurablePermitState.ISSUED,
            issued_at=current_time,
        )
        decision = AuthorityDecision(
            decision=Decision.AUTHORIZED,
            proposal_id=proposal.proposal_id,
            reason_code="AUTHORIZED_WITH_DURABLE_SINGLE_USE_PERMIT",
            policy_version=POLICY_VERSION,
            permit_id=permit_id,
        )
        self.store.persist_authorization(
            proposal,
            decision,
            permit,
            created_at=current_time,
        )
        self.audit.append("AUTHORITY_GRANTED", decision.__dict__)
        return decision

    def execute(
        self,
        proposal: Proposal,
        permit_id: str,
        *,
        now: datetime | None = None,
    ) -> ExecutionReceipt:
        current_time = self._now(now)
        consume = self.store.consume_permit(
            proposal,
            permit_id,
            now=current_time,
        )

        if consume.decision is not Decision.AUTHORIZED:
            state_version = self.pipeline.snapshot().state_version
            receipt = ExecutionReceipt(
                decision=consume.decision,
                proposal_id=proposal.proposal_id,
                permit_id=permit_id,
                reason_code=consume.reason_code,
                state_version_before=state_version,
                state_version_after=state_version,
            )
            self.store.persist_execution(receipt, created_at=current_time)
            self.audit.append("EXECUTION_DENIED", receipt.__dict__)
            return receipt

        before = self.pipeline.snapshot()
        self.audit.append(
            "PERMIT_CONSUMED",
            {
                "permit_id": permit_id,
                "proposal_id": proposal.proposal_id,
                "incident_id": proposal.incident_id,
                "bound_state_version": before.state_version,
            },
        )
        self.audit.append(
            "EXECUTION_STARTED",
            {
                "permit_id": permit_id,
                "proposal_id": proposal.proposal_id,
                "action": proposal.action.value,
                "target": proposal.target,
            },
        )

        try:
            after, postconditions = self.pipeline._execute_authorized(
                proposal.action,
                proposal.target,
            )
        except Exception as exc:
            self.store.mark_permit_execution_failed(permit_id, now=current_time)
            failure = ExecutionReceipt(
                decision=Decision.DENIED,
                proposal_id=proposal.proposal_id,
                permit_id=permit_id,
                reason_code="EXECUTION_FAILED_AFTER_PERMIT_CONSUMPTION",
                state_version_before=before.state_version,
                state_version_after=self.pipeline.snapshot().state_version,
            )
            self.store.persist_execution(failure, created_at=current_time)
            self.audit.append(
                "EXECUTION_FAILED",
                {
                    **failure.__dict__,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        # These writes occur only after the external side effect returned.
        self.store.persist_incident(after)
        self.store.mark_permit_executed(permit_id, now=current_time)

        receipt = ExecutionReceipt(
            decision=Decision.AUTHORIZED,
            proposal_id=proposal.proposal_id,
            permit_id=permit_id,
            reason_code="EXECUTED_WITH_DURABLE_SINGLE_USE_PERMIT",
            state_version_before=before.state_version,
            state_version_after=after.state_version,
            postconditions=postconditions,
        )
        self.store.persist_execution(receipt, created_at=current_time)
        self.audit.append("EXECUTION_SUCCEEDED", receipt.__dict__)
        return receipt
