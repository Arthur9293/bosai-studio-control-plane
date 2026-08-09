from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

from google.cloud import firestore

from .audit import AuditEvent
from .contracts import Action, AuthorityDecision, AuthorityGrant, Decision, ExecutionReceipt, Proposal
from .pipeline import PipelineState


AUTHORITY_RUN_COLLECTION = "bosai_authority_runs"
POLICY_ID = "studio-recovery-policy"


class DurablePermitState(StrEnum):
    ISSUED = "ISSUED"
    CONSUMED_PENDING = "CONSUMED_PENDING"
    EXECUTED = "EXECUTED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True)
class DurablePermitRecord:
    permit_id: str
    proposal_id: str
    incident_id: str
    action: Action
    target: str
    policy_version: str
    bound_state_version: int
    expires_at: datetime
    status: DurablePermitState = DurablePermitState.ISSUED
    issued_at: datetime | None = None
    consumed_at: datetime | None = None
    terminal_at: datetime | None = None


@dataclass(frozen=True)
class ConsumePermitResult:
    decision: Decision
    reason_code: str
    permit_state: DurablePermitState | None


class AuthorityStateStore(Protocol):
    namespace: str

    def persist_incident(self, state: PipelineState) -> None: ...

    def persist_policy(self, grant: AuthorityGrant) -> None: ...

    def persist_proposal(self, proposal: Proposal, *, created_at: datetime) -> None: ...

    def persist_decision(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        *,
        created_at: datetime,
    ) -> None: ...

    def persist_authorization(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        permit: DurablePermitRecord,
        *,
        created_at: datetime,
    ) -> None: ...

    def get_permit(self, permit_id: str) -> DurablePermitRecord | None: ...

    def consume_permit(
        self,
        proposal: Proposal,
        permit_id: str,
        *,
        now: datetime,
    ) -> ConsumePermitResult: ...

    def mark_permit_executed(self, permit_id: str, *, now: datetime) -> None: ...

    def mark_permit_execution_failed(self, permit_id: str, *, now: datetime) -> None: ...

    def persist_execution(self, receipt: ExecutionReceipt, *, created_at: datetime) -> str: ...

    def append_audit(self, event_type: str, payload: dict[str, Any]) -> AuditEvent: ...

    def list_audit_events(self) -> tuple[AuditEvent, ...]: ...

    def verify_audit(self) -> bool: ...

    def permit_count_for_proposal(self, proposal_id: str) -> int: ...

    def summary(self) -> dict[str, object]: ...


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _normalize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalize(item) for item in value]
    return value


def _proposal_dict(proposal: Proposal, created_at: datetime) -> dict[str, Any]:
    return {
        "proposal_id": proposal.proposal_id,
        "incident_id": proposal.incident_id,
        "action": proposal.action.value,
        "target": proposal.target,
        "reason": proposal.reason,
        "evidence_refs": list(proposal.evidence_refs),
        "expected_postconditions": list(proposal.expected_postconditions),
        "created_at": created_at,
    }


def _decision_dict(
    proposal: Proposal,
    decision: AuthorityDecision,
    created_at: datetime,
) -> dict[str, Any]:
    return {
        "proposal_id": proposal.proposal_id,
        "incident_id": proposal.incident_id,
        "action": proposal.action.value,
        "target": proposal.target,
        "decision": decision.decision.value,
        "reason_code": decision.reason_code,
        "policy_version": decision.policy_version,
        "violated_invariant": decision.violated_invariant,
        "permit_id": decision.permit_id,
        "created_at": created_at,
    }


def _permit_dict(permit: DurablePermitRecord) -> dict[str, Any]:
    return {
        "permit_id": permit.permit_id,
        "proposal_id": permit.proposal_id,
        "incident_id": permit.incident_id,
        "action": permit.action.value,
        "target": permit.target,
        "policy_version": permit.policy_version,
        "bound_state_version": permit.bound_state_version,
        "expires_at": permit.expires_at,
        "status": permit.status.value,
        "issued_at": permit.issued_at,
        "consumed_at": permit.consumed_at,
        "terminal_at": permit.terminal_at,
    }


def _permit_from_dict(data: dict[str, Any]) -> DurablePermitRecord:
    return DurablePermitRecord(
        permit_id=str(data["permit_id"]),
        proposal_id=str(data["proposal_id"]),
        incident_id=str(data["incident_id"]),
        action=Action(str(data["action"])),
        target=str(data["target"]),
        policy_version=str(data["policy_version"]),
        bound_state_version=int(data["bound_state_version"]),
        expires_at=data["expires_at"],
        status=DurablePermitState(str(data["status"])),
        issued_at=data.get("issued_at"),
        consumed_at=data.get("consumed_at"),
        terminal_at=data.get("terminal_at"),
    )


def _execution_dict(receipt: ExecutionReceipt, created_at: datetime) -> dict[str, Any]:
    return {
        "proposal_id": receipt.proposal_id,
        "permit_id": receipt.permit_id,
        "decision": receipt.decision.value,
        "reason_code": receipt.reason_code,
        "state_version_before": receipt.state_version_before,
        "state_version_after": receipt.state_version_after,
        "postconditions": list(receipt.postconditions),
        "created_at": created_at,
    }


def _audit_event_from_dict(data: dict[str, Any]) -> AuditEvent:
    return AuditEvent(
        event_id=str(data["event_id"]),
        sequence=int(data["sequence"]),
        event_type=str(data["event_type"]),
        payload=dict(data["payload"]),
        previous_event_hash=str(data["previous_event_hash"]),
        payload_digest=str(data["payload_digest"]),
        event_hash=str(data["event_hash"]),
    )


def _verify_audit_events(events: tuple[AuditEvent, ...]) -> bool:
    previous = "GENESIS"
    for index, event in enumerate(events, start=1):
        if event.sequence != index or event.previous_event_hash != previous:
            return False
        if sha256(_canonical(event.payload)).hexdigest() != event.payload_digest:
            return False
        material = {
            "sequence": event.sequence,
            "event_type": event.event_type,
            "payload_digest": event.payload_digest,
            "previous_event_hash": event.previous_event_hash,
        }
        if sha256(_canonical(material)).hexdigest() != event.event_hash:
            return False
        previous = event.event_hash
    return True


class InMemoryAuthorityStateStore:
    """Deterministic durable-store analogue used to exercise Phase 7 semantics locally."""

    def __init__(self, namespace: str = "test", *, simulated_transaction_retries: int = 0) -> None:
        self.namespace = namespace
        self.simulated_transaction_retries = simulated_transaction_retries
        self.transaction_attempts = 0
        self._lock = Lock()
        self._incidents: dict[str, dict[str, Any]] = {}
        self._policies: dict[str, dict[str, Any]] = {}
        self._proposals: dict[str, dict[str, Any]] = {}
        self._decisions: dict[str, dict[str, Any]] = {}
        self._permits: dict[str, dict[str, Any]] = {}
        self._executions: dict[str, dict[str, Any]] = {}
        self._audit_events: list[AuditEvent] = []

    def persist_incident(self, state: PipelineState) -> None:
        with self._lock:
            self._incidents[state.incident_id] = _normalize(asdict(state))

    def persist_policy(self, grant: AuthorityGrant) -> None:
        with self._lock:
            self._policies[grant.policy_version] = {
                "policy_id": POLICY_ID,
                "policy_version": grant.policy_version,
                "grant_id": grant.grant_id,
                "allowed_actions": sorted(action.value for action in grant.allowed_actions),
                "expires_at": grant.expires_at,
            }

    def persist_proposal(self, proposal: Proposal, *, created_at: datetime) -> None:
        with self._lock:
            self._proposals[proposal.proposal_id] = _proposal_dict(proposal, created_at)

    def persist_decision(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        *,
        created_at: datetime,
    ) -> None:
        with self._lock:
            self._decisions[proposal.proposal_id] = _decision_dict(proposal, decision, created_at)

    def persist_authorization(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        permit: DurablePermitRecord,
        *,
        created_at: datetime,
    ) -> None:
        with self._lock:
            self._decisions[proposal.proposal_id] = _decision_dict(proposal, decision, created_at)
            if permit.permit_id in self._permits:
                raise RuntimeError(f"permit already exists: {permit.permit_id}")
            self._permits[permit.permit_id] = _permit_dict(permit)

    def get_permit(self, permit_id: str) -> DurablePermitRecord | None:
        with self._lock:
            data = self._permits.get(permit_id)
            return _permit_from_dict(dict(data)) if data else None

    def consume_permit(
        self,
        proposal: Proposal,
        permit_id: str,
        *,
        now: datetime,
    ) -> ConsumePermitResult:
        with self._lock:
            for attempt in range(self.simulated_transaction_retries + 1):
                self.transaction_attempts += 1
                data = self._permits.get(permit_id)
                if data is None:
                    return ConsumePermitResult(Decision.DENIED, "PERMIT_NOT_FOUND", None)

                permit = _permit_from_dict(dict(data))
                if permit.status is not DurablePermitState.ISSUED:
                    return ConsumePermitResult(
                        Decision.DENIED_REPLAY,
                        "PERMIT_ALREADY_CONSUMED",
                        permit.status,
                    )
                if now >= permit.expires_at:
                    data["status"] = DurablePermitState.EXPIRED.value
                    data["terminal_at"] = now
                    return ConsumePermitResult(Decision.DENIED, "PERMIT_EXPIRED", DurablePermitState.EXPIRED)
                if (
                    permit.proposal_id != proposal.proposal_id
                    or permit.incident_id != proposal.incident_id
                    or permit.action is not proposal.action
                    or permit.target != proposal.target
                ):
                    data["status"] = DurablePermitState.INVALIDATED.value
                    data["terminal_at"] = now
                    return ConsumePermitResult(
                        Decision.DENIED,
                        "PERMIT_BINDING_MISMATCH",
                        DurablePermitState.INVALIDATED,
                    )

                incident = self._incidents.get(permit.incident_id)
                if incident is None or int(incident["state_version"]) != permit.bound_state_version:
                    data["status"] = DurablePermitState.INVALIDATED.value
                    data["terminal_at"] = now
                    return ConsumePermitResult(
                        Decision.REEVALUATION_REQUIRED,
                        "TRAJECTORY_STATE_CHANGED",
                        DurablePermitState.INVALIDATED,
                    )

                if attempt < self.simulated_transaction_retries:
                    continue

                data["status"] = DurablePermitState.CONSUMED_PENDING.value
                data["consumed_at"] = now
                return ConsumePermitResult(
                    Decision.AUTHORIZED,
                    "PERMIT_CONSUMED_PENDING",
                    DurablePermitState.CONSUMED_PENDING,
                )

        raise AssertionError("consume_permit loop exited unexpectedly")

    def mark_permit_executed(self, permit_id: str, *, now: datetime) -> None:
        with self._lock:
            data = self._permits[permit_id]
            if data["status"] != DurablePermitState.CONSUMED_PENDING.value:
                raise RuntimeError(f"permit not pending execution: {permit_id}")
            data["status"] = DurablePermitState.EXECUTED.value
            data["terminal_at"] = now

    def mark_permit_execution_failed(self, permit_id: str, *, now: datetime) -> None:
        with self._lock:
            data = self._permits[permit_id]
            data["status"] = DurablePermitState.EXECUTION_FAILED.value
            data["terminal_at"] = now

    def persist_execution(self, receipt: ExecutionReceipt, *, created_at: datetime) -> str:
        execution_id = f"execution-{uuid4().hex}"
        with self._lock:
            self._executions[execution_id] = _execution_dict(receipt, created_at)
        return execution_id

    def append_audit(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        normalized = _normalize(payload)
        with self._lock:
            sequence = len(self._audit_events) + 1
            previous = self._audit_events[-1].event_hash if self._audit_events else "GENESIS"
            payload_digest = sha256(_canonical(normalized)).hexdigest()
            material = {
                "sequence": sequence,
                "event_type": event_type,
                "payload_digest": payload_digest,
                "previous_event_hash": previous,
            }
            event_hash = sha256(_canonical(material)).hexdigest()
            event = AuditEvent(
                event_id=f"audit-{sequence:08d}",
                sequence=sequence,
                event_type=event_type,
                payload=normalized,
                previous_event_hash=previous,
                payload_digest=payload_digest,
                event_hash=event_hash,
            )
            self._audit_events.append(event)
            return event

    def list_audit_events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._audit_events)

    def verify_audit(self) -> bool:
        return _verify_audit_events(self.list_audit_events())

    def permit_count_for_proposal(self, proposal_id: str) -> int:
        with self._lock:
            return sum(1 for data in self._permits.values() if data["proposal_id"] == proposal_id)

    def summary(self) -> dict[str, object]:
        with self._lock:
            return {
                "namespace": self.namespace,
                "incidents": len(self._incidents),
                "policies": len(self._policies),
                "proposals": len(self._proposals),
                "decisions": len(self._decisions),
                "permits": len(self._permits),
                "executions": len(self._executions),
                "audit_events": len(self._audit_events),
                "audit_chain_valid": _verify_audit_events(tuple(self._audit_events)),
                "transaction_attempts": self.transaction_attempts,
            }


class FirestoreAuthorityStateStore:
    """Cloud Firestore implementation of the bounded BOSAI authority state model."""

    def __init__(
        self,
        *,
        project: str,
        namespace: str,
        client: firestore.Client | None = None,
    ) -> None:
        self.namespace = namespace
        self.client = client or firestore.Client(project=project)
        self._root = self.client.collection(AUTHORITY_RUN_COLLECTION).document(namespace)

    def _collection(self, name: str):
        return self._root.collection(name)

    def persist_incident(self, state: PipelineState) -> None:
        self._collection("incidents").document(state.incident_id).set(_normalize(asdict(state)))

    def persist_policy(self, grant: AuthorityGrant) -> None:
        (
            self._collection("policies")
            .document(POLICY_ID)
            .collection("versions")
            .document(grant.policy_version)
            .set(
                {
                    "policy_id": POLICY_ID,
                    "policy_version": grant.policy_version,
                    "grant_id": grant.grant_id,
                    "allowed_actions": sorted(action.value for action in grant.allowed_actions),
                    "expires_at": grant.expires_at,
                }
            )
        )

    def persist_proposal(self, proposal: Proposal, *, created_at: datetime) -> None:
        self._collection("proposals").document(proposal.proposal_id).set(
            _proposal_dict(proposal, created_at)
        )

    def persist_decision(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        *,
        created_at: datetime,
    ) -> None:
        self._collection("decisions").document(proposal.proposal_id).set(
            _decision_dict(proposal, decision, created_at)
        )

    def persist_authorization(
        self,
        proposal: Proposal,
        decision: AuthorityDecision,
        permit: DurablePermitRecord,
        *,
        created_at: datetime,
    ) -> None:
        batch = self.client.batch()
        batch.set(
            self._collection("decisions").document(proposal.proposal_id),
            _decision_dict(proposal, decision, created_at),
        )
        batch.create(
            self._collection("permits").document(permit.permit_id),
            _permit_dict(permit),
        )
        batch.commit()

    def get_permit(self, permit_id: str) -> DurablePermitRecord | None:
        snapshot = self._collection("permits").document(permit_id).get()
        if not snapshot.exists:
            return None
        return _permit_from_dict(snapshot.to_dict() or {})

    def consume_permit(
        self,
        proposal: Proposal,
        permit_id: str,
        *,
        now: datetime,
    ) -> ConsumePermitResult:
        permit_ref = self._collection("permits").document(permit_id)
        transaction = self.client.transaction(max_attempts=5)

        @firestore.transactional
        def consume_in_transaction(txn):
            permit_snapshot = permit_ref.get(transaction=txn)
            if not permit_snapshot.exists:
                return ConsumePermitResult(Decision.DENIED, "PERMIT_NOT_FOUND", None)

            permit_data = permit_snapshot.to_dict() or {}
            permit = _permit_from_dict(permit_data)
            incident_ref = self._collection("incidents").document(permit.incident_id)
            incident_snapshot = incident_ref.get(transaction=txn)

            if permit.status is not DurablePermitState.ISSUED:
                return ConsumePermitResult(
                    Decision.DENIED_REPLAY,
                    "PERMIT_ALREADY_CONSUMED",
                    permit.status,
                )
            if now >= permit.expires_at:
                txn.update(
                    permit_ref,
                    {"status": DurablePermitState.EXPIRED.value, "terminal_at": now},
                )
                return ConsumePermitResult(Decision.DENIED, "PERMIT_EXPIRED", DurablePermitState.EXPIRED)
            if (
                permit.proposal_id != proposal.proposal_id
                or permit.incident_id != proposal.incident_id
                or permit.action is not proposal.action
                or permit.target != proposal.target
            ):
                txn.update(
                    permit_ref,
                    {"status": DurablePermitState.INVALIDATED.value, "terminal_at": now},
                )
                return ConsumePermitResult(
                    Decision.DENIED,
                    "PERMIT_BINDING_MISMATCH",
                    DurablePermitState.INVALIDATED,
                )

            incident_data = incident_snapshot.to_dict() if incident_snapshot.exists else None
            if incident_data is None or int(incident_data["state_version"]) != permit.bound_state_version:
                txn.update(
                    permit_ref,
                    {"status": DurablePermitState.INVALIDATED.value, "terminal_at": now},
                )
                return ConsumePermitResult(
                    Decision.REEVALUATION_REQUIRED,
                    "TRAJECTORY_STATE_CHANGED",
                    DurablePermitState.INVALIDATED,
                )

            txn.update(
                permit_ref,
                {
                    "status": DurablePermitState.CONSUMED_PENDING.value,
                    "consumed_at": now,
                },
            )
            return ConsumePermitResult(
                Decision.AUTHORIZED,
                "PERMIT_CONSUMED_PENDING",
                DurablePermitState.CONSUMED_PENDING,
            )

        return consume_in_transaction(transaction)

    def mark_permit_executed(self, permit_id: str, *, now: datetime) -> None:
        self._collection("permits").document(permit_id).update(
            {"status": DurablePermitState.EXECUTED.value, "terminal_at": now}
        )

    def mark_permit_execution_failed(self, permit_id: str, *, now: datetime) -> None:
        self._collection("permits").document(permit_id).update(
            {"status": DurablePermitState.EXECUTION_FAILED.value, "terminal_at": now}
        )

    def persist_execution(self, receipt: ExecutionReceipt, *, created_at: datetime) -> str:
        execution_id = f"execution-{uuid4().hex}"
        self._collection("executions").document(execution_id).set(
            _execution_dict(receipt, created_at)
        )
        return execution_id

    def append_audit(self, event_type: str, payload: dict[str, Any]) -> AuditEvent:
        normalized = _normalize(payload)
        meta_ref = self._collection("meta").document("audit")
        transaction = self.client.transaction(max_attempts=5)

        @firestore.transactional
        def append_in_transaction(txn):
            meta_snapshot = meta_ref.get(transaction=txn)
            meta = meta_snapshot.to_dict() if meta_snapshot.exists else {}
            sequence = int(meta.get("sequence", 0)) + 1
            previous = str(meta.get("head", "GENESIS"))
            payload_digest = sha256(_canonical(normalized)).hexdigest()
            material = {
                "sequence": sequence,
                "event_type": event_type,
                "payload_digest": payload_digest,
                "previous_event_hash": previous,
            }
            event_hash = sha256(_canonical(material)).hexdigest()
            event = AuditEvent(
                event_id=f"audit-{sequence:08d}",
                sequence=sequence,
                event_type=event_type,
                payload=normalized,
                previous_event_hash=previous,
                payload_digest=payload_digest,
                event_hash=event_hash,
            )
            event_ref = self._collection("audit_events").document(event.event_id)
            txn.set(event_ref, _normalize(asdict(event)))
            txn.set(meta_ref, {"sequence": sequence, "head": event_hash})
            return event

        return append_in_transaction(transaction)

    def list_audit_events(self) -> tuple[AuditEvent, ...]:
        snapshots = self._collection("audit_events").order_by("sequence").stream()
        return tuple(_audit_event_from_dict(snapshot.to_dict() or {}) for snapshot in snapshots)

    def verify_audit(self) -> bool:
        return _verify_audit_events(self.list_audit_events())

    def permit_count_for_proposal(self, proposal_id: str) -> int:
        return sum(
            1
            for snapshot in self._collection("permits").stream()
            if (snapshot.to_dict() or {}).get("proposal_id") == proposal_id
        )

    def summary(self) -> dict[str, object]:
        collections = (
            "incidents",
            "proposals",
            "decisions",
            "permits",
            "executions",
            "audit_events",
        )
        counts = {
            name: sum(1 for _ in self._collection(name).stream())
            for name in collections
        }
        return {
            "namespace": self.namespace,
            **counts,
            "audit_chain_valid": self.verify_audit(),
        }
