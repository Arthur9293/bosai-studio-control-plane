from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from .authority import AuthorityExecutor, POLICY_VERSION
from .contracts import Action, AuthorityGrant, Proposal
from .observed_pipeline import ObservedMediaPipelineSim
from .telemetry import PipelineTelemetry


def _proposal(proposal_id: str, action: Action, target: str, reason: str) -> Proposal:
    return Proposal(
        proposal_id=proposal_id,
        incident_id="incident-demo-001",
        action=action,
        target=target,
        reason=reason,
        evidence_refs=("grafana-phase4-telemetry",),
    )


def run_grafana_smoke_scenario(telemetry: PipelineTelemetry) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    pipeline = ObservedMediaPipelineSim(telemetry)
    grant = AuthorityGrant(
        grant_id="grant-grafana-phase4",
        allowed_actions=frozenset(Action),
        expires_at=now + timedelta(minutes=10),
        policy_version=POLICY_VERSION,
    )
    executor = AuthorityExecutor(pipeline, grant=grant)

    pipeline.emit_initial_incident()

    restart = _proposal(
        "proposal-grafana-restart",
        Action.RESTART_TRANSCODE_WORKER,
        "transcode-a",
        "primary transcode worker is unhealthy",
    )
    restart_decision = executor.evaluate(restart, now=now)
    restart_receipt = executor.execute(restart, restart_decision.permit_id or "", now=now)

    disable_qc = _proposal(
        "proposal-grafana-qc-bypass",
        Action.DISABLE_QUALITY_CONTROL_VALIDATION,
        "quality-control",
        "reduce delivery latency while SLA remains at risk",
    )
    qc_decision = executor.evaluate(disable_qc, now=now)

    reroute = _proposal(
        "proposal-grafana-reroute",
        Action.REROUTE_TRANSCODE_WORKLOAD,
        "transcode-b",
        "healthy alternate capacity is available",
    )
    reroute_decision = executor.evaluate(reroute, now=now)
    reroute_receipt = executor.execute(reroute, reroute_decision.permit_id or "", now=now)

    flushed = telemetry.force_flush()
    state = pipeline.snapshot()
    return {
        "synthetic": True,
        "service_name": "bosai-studio-media-pipeline",
        "restart_decision": str(restart_decision.decision),
        "restart_execution": str(restart_receipt.decision),
        "qc_bypass_decision": str(qc_decision.decision),
        "qc_bypass_invariant": qc_decision.violated_invariant,
        "reroute_decision": str(reroute_decision.decision),
        "reroute_execution": str(reroute_receipt.decision),
        "active_worker": state.active_worker,
        "sla_at_risk": state.sla_at_risk,
        "fresh_qc_pass": state.fresh_qc_pass,
        "telemetry_force_flush": flushed,
    }


def main() -> None:
    telemetry = PipelineTelemetry.from_otlp_env()
    try:
        print(json.dumps(run_grafana_smoke_scenario(telemetry), indent=2, sort_keys=True))
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
