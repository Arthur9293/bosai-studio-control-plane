from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from .authority import AuthorityExecutor, POLICY_VERSION
from .contracts import Action, AuthorityGrant, Proposal
from .pipeline import MediaPipelineSim


def build_demo() -> tuple[AuthorityExecutor, datetime]:
    now = datetime(2026, 8, 9, 13, 30, tzinfo=timezone.utc)
    pipeline = MediaPipelineSim()
    grant = AuthorityGrant(
        grant_id="grant-demo-001",
        allowed_actions=frozenset(Action),
        expires_at=now + timedelta(hours=1),
        policy_version=POLICY_VERSION,
    )
    return AuthorityExecutor(pipeline, grant=grant), now


def proposal(proposal_id: str, action: Action, target: str, reason: str) -> Proposal:
    return Proposal(
        proposal_id=proposal_id,
        incident_id="incident-demo-001",
        action=action,
        target=target,
        reason=reason,
        evidence_refs=("synthetic-evidence",),
    )


def run_vertical_slice() -> dict[str, object]:
    executor, now = build_demo()

    restart = proposal("proposal-001", Action.RESTART_TRANSCODE_WORKER, "transcode-a", "primary worker unhealthy")
    restart_decision = executor.evaluate(restart, now=now)
    restart_receipt = executor.execute(restart, restart_decision.permit_id or "", now=now)

    disable_qc = proposal(
        "proposal-002",
        Action.DISABLE_QUALITY_CONTROL_VALIDATION,
        "quality-control",
        "reduce delivery latency while SLA remains at risk",
    )
    disable_qc_decision = executor.evaluate(disable_qc, now=now)

    reroute = proposal("proposal-003", Action.REROUTE_TRANSCODE_WORKLOAD, "transcode-b", "alternate worker healthy")
    reroute_decision = executor.evaluate(reroute, now=now)
    reroute_receipt = executor.execute(reroute, reroute_decision.permit_id or "", now=now)
    replay_receipt = executor.execute(reroute, reroute_decision.permit_id or "", now=now)

    state = executor.pipeline.snapshot()
    return {
        "restart_decision": restart_decision.decision,
        "restart_execution": restart_receipt.decision,
        "disable_qc_decision": disable_qc_decision.decision,
        "disable_qc_invariant": disable_qc_decision.violated_invariant,
        "reroute_decision": reroute_decision.decision,
        "reroute_execution": reroute_receipt.decision,
        "replay_decision": replay_receipt.decision,
        "active_worker": state.active_worker,
        "sla_at_risk": state.sla_at_risk,
        "qc_validation_enabled": state.qc_validation_enabled,
        "fresh_qc_pass": state.fresh_qc_pass,
        "audit_chain_valid": executor.audit.verify(),
        "audit_event_count": len(executor.audit.events),
    }


if __name__ == "__main__":
    print(json.dumps(run_vertical_slice(), indent=2, default=str, sort_keys=True))
