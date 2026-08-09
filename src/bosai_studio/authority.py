from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock

from .audit import AuditTrail
from .contracts import (
    Action,
    AuthorityDecision,
    AuthorityGrant,
    Decision,
    ExecutionReceipt,
    Permit,
    PermitState,
    Proposal,
)
from .pipeline import MediaPipelineSim, PipelineState


POLICY_VERSION = "bsc-demo-policy-v1"
INVARIANT_FRESH_QC = "FINAL_RELEASE_INTENT_AND_NOT_FRESH_QC_PASS=>QC_VALIDATION_ENABLED"


class AuthorityExecutor:
    """Deterministic authority boundary. It is deliberately not an AI component."""

    def __init__(
        self,
        pipeline: MediaPipelineSim,
        *,
        grant: AuthorityGrant,
        permit_ttl: timedelta = timedelta(minutes=2),
    ) -> None:
        self.pipeline = pipeline
        self.grant = grant
        self.permit_ttl = permit_ttl
        self.audit = AuditTrail()
        self._permits: dict[str, Permit] = {}
        self._permit_counter = 0
        self._lock = Lock()

    @staticmethod
    def _now(now: datetime | None) -> datetime:
        return now or datetime.now(timezone.utc)

    def _deny(
        self,
        proposal: Proposal,
        reason_code: str,
        *,
        violated_invariant: str | None = None,
    ) -> AuthorityDecision:
        decision = AuthorityDecision(
            decision=Decision.DENIED,
            proposal_id=proposal.proposal_id,
            reason_code=reason_code,
            policy_version=POLICY_VERSION,
            violated_invariant=violated_invariant,
        )
        self.audit.append("AUTHORITY_DECISION", decision.__dict__)
        return decision

    def evaluate(self, proposal: Proposal, *, now: datetime | None = None) -> AuthorityDecision:
        current_time = self._now(now)
        state = self.pipeline.snapshot()

        if self.grant.policy_version != POLICY_VERSION:
            return self._deny(proposal, "GRANT_POLICY_VERSION_MISMATCH")
        if current_time >= self.grant.expires_at:
            return self._deny(proposal, "AUTHORITY_GRANT_EXPIRED")
        if proposal.action not in self.grant.allowed_actions:
            return self._deny(proposal, "ACTION_OUTSIDE_AUTHORITY_GRANT")
        if proposal.incident_id != state.incident_id:
            return self._deny(proposal, "INCIDENT_SCOPE_MISMATCH")

        local_error = self._check_local_predicates(proposal, state)
        if local_error:
            return self._deny(proposal, local_error)

        violated = self._check_global_invariants(proposal, state)
        if violated:
            return self._deny(proposal, "GLOBAL_TRAJECTORY_INVARIANT_VIOLATION", violated_invariant=violated)

        with self._lock:
            self._permit_counter += 1
            permit_id = f"permit-{self._permit_counter:04d}"
            permit = Permit(
                permit_id=permit_id,
                proposal_id=proposal.proposal_id,
                incident_id=proposal.incident_id,
                action=proposal.action,
                target=proposal.target,
                policy_version=POLICY_VERSION,
                bound_state_version=state.state_version,
                expires_at=current_time + self.permit_ttl,
            )
            self._permits[permit_id] = permit

        decision = AuthorityDecision(
            decision=Decision.AUTHORIZED,
            proposal_id=proposal.proposal_id,
            reason_code="AUTHORIZED_WITH_SINGLE_USE_PERMIT",
            policy_version=POLICY_VERSION,
            permit_id=permit_id,
        )
        self.audit.append("AUTHORITY_DECISION", decision.__dict__)
        return decision

    @staticmethod
    def _check_local_predicates(proposal: Proposal, state: PipelineState) -> str | None:
        if proposal.action is Action.RESTART_TRANSCODE_WORKER:
            if proposal.target != "transcode-a":
                return "RESTART_TARGET_NOT_ALLOWED"
            if state.transcode_a_health not in {"UNHEALTHY", "DEGRADED"}:
                return "RESTART_NOT_NEEDED"
            return None

        if proposal.action is Action.REROUTE_TRANSCODE_WORKLOAD:
            if proposal.target != "transcode-b":
                return "REROUTE_TARGET_NOT_ALLOWED"
            if state.transcode_b_health != "HEALTHY":
                return "REROUTE_TARGET_UNHEALTHY"
            if state.active_worker == "transcode-b":
                return "REROUTE_ALREADY_APPLIED"
            return None

        if proposal.action is Action.DISABLE_QUALITY_CONTROL_VALIDATION:
            if not state.qc_validation_enabled:
                return "QC_ALREADY_DISABLED"
            return None

        return "UNKNOWN_ACTION"

    @staticmethod
    def _check_global_invariants(proposal: Proposal, state: PipelineState) -> str | None:
        projected_qc_enabled = state.qc_validation_enabled
        if proposal.action is Action.DISABLE_QUALITY_CONTROL_VALIDATION:
            projected_qc_enabled = False

        if state.release_intent and not state.fresh_qc_pass and not projected_qc_enabled:
            return INVARIANT_FRESH_QC
        return None

    def execute(self, proposal: Proposal, permit_id: str, *, now: datetime | None = None) -> ExecutionReceipt:
        current_time = self._now(now)

        with self._lock:
            permit = self._permits.get(permit_id)
            if permit is None:
                return self._execution_denial(proposal, permit_id, Decision.DENIED, "PERMIT_NOT_FOUND")
            if permit.state is not PermitState.ISSUED:
                return self._execution_denial(proposal, permit_id, Decision.DENIED_REPLAY, "PERMIT_ALREADY_CONSUMED")
            if current_time >= permit.expires_at:
                permit.state = PermitState.FAILED
                return self._execution_denial(proposal, permit_id, Decision.DENIED, "PERMIT_EXPIRED")
            if (
                permit.proposal_id != proposal.proposal_id
                or permit.incident_id != proposal.incident_id
                or permit.action is not proposal.action
                or permit.target != proposal.target
            ):
                return self._execution_denial(proposal, permit_id, Decision.DENIED, "PERMIT_BINDING_MISMATCH")

            before = self.pipeline.snapshot()
            if before.state_version != permit.bound_state_version:
                permit.state = PermitState.FAILED
                return self._execution_denial(
                    proposal,
                    permit_id,
                    Decision.REEVALUATION_REQUIRED,
                    "TRAJECTORY_STATE_CHANGED",
                )

            # Atomic local analogue of future Firestore permit consumption.
            permit.state = PermitState.CONSUMED_PENDING

        before_version = before.state_version
        try:
            after, postconditions = self.pipeline.execute_authorized(proposal.action, proposal.target)
        except Exception:
            with self._lock:
                permit.state = PermitState.FAILED
            raise

        with self._lock:
            permit.state = PermitState.EXECUTED

        receipt = ExecutionReceipt(
            decision=Decision.AUTHORIZED,
            proposal_id=proposal.proposal_id,
            permit_id=permit_id,
            reason_code="EXECUTED_WITH_VALID_SINGLE_USE_PERMIT",
            state_version_before=before_version,
            state_version_after=after.state_version,
            postconditions=postconditions,
        )
        self.audit.append("EXECUTION_RECEIPT", receipt.__dict__)
        return receipt

    def _execution_denial(
        self,
        proposal: Proposal,
        permit_id: str | None,
        decision: Decision,
        reason_code: str,
    ) -> ExecutionReceipt:
        state_version = self.pipeline.snapshot().state_version
        receipt = ExecutionReceipt(
            decision=decision,
            proposal_id=proposal.proposal_id,
            permit_id=permit_id,
            reason_code=reason_code,
            state_version_before=state_version,
            state_version_after=state_version,
        )
        self.audit.append("EXECUTION_DENIAL", receipt.__dict__)
        return receipt
