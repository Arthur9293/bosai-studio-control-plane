from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Action(StrEnum):
    RESTART_TRANSCODE_WORKER = "RESTART_TRANSCODE_WORKER"
    DISABLE_QUALITY_CONTROL_VALIDATION = "DISABLE_QUALITY_CONTROL_VALIDATION"
    REROUTE_TRANSCODE_WORKLOAD = "REROUTE_TRANSCODE_WORKLOAD"


class Decision(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    DENIED_REPLAY = "DENIED_REPLAY"
    REEVALUATION_REQUIRED = "REEVALUATION_REQUIRED"


class PermitState(StrEnum):
    ISSUED = "ISSUED"
    CONSUMED_PENDING = "CONSUMED_PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    incident_id: str
    action: Action
    target: str
    reason: str
    evidence_refs: tuple[str, ...] = ()
    expected_postconditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    allowed_actions: frozenset[Action]
    expires_at: datetime
    policy_version: str


@dataclass(frozen=True)
class AuthorityDecision:
    decision: Decision
    proposal_id: str
    reason_code: str
    policy_version: str
    violated_invariant: str | None = None
    permit_id: str | None = None


@dataclass
class Permit:
    permit_id: str
    proposal_id: str
    incident_id: str
    action: Action
    target: str
    policy_version: str
    bound_state_version: int
    expires_at: datetime
    state: PermitState = PermitState.ISSUED


@dataclass(frozen=True)
class ExecutionReceipt:
    decision: Decision
    proposal_id: str
    permit_id: str | None
    reason_code: str
    state_version_before: int
    state_version_after: int
    postconditions: tuple[str, ...] = field(default_factory=tuple)
