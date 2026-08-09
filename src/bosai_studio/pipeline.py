from __future__ import annotations

from dataclasses import dataclass, replace

from .contracts import Action


@dataclass(frozen=True)
class PipelineState:
    incident_id: str = "incident-demo-001"
    state_version: int = 1
    active_worker: str = "transcode-a"
    transcode_a_health: str = "UNHEALTHY"
    transcode_b_health: str = "HEALTHY"
    sla_at_risk: bool = True
    release_intent: bool = True
    qc_validation_enabled: bool = True
    latest_transform_seq: int = 10
    last_qc_pass_seq: int = 8

    @property
    def fresh_qc_pass(self) -> bool:
        return self.last_qc_pass_seq >= self.latest_transform_seq


class MediaPipelineSim:
    """Deterministic synthetic trailer pipeline used only for the hackathon vertical slice."""

    def __init__(self, state: PipelineState | None = None) -> None:
        self._state = state or PipelineState()

    def snapshot(self) -> PipelineState:
        return self._state

    def _replace(self, **changes: object) -> PipelineState:
        changes["state_version"] = self._state.state_version + 1
        self._state = replace(self._state, **changes)
        return self._state

    def _execute_authorized(self, action: Action, target: str) -> tuple[PipelineState, tuple[str, ...]]:
        """Internal mutation primitive; AuthorityExecutor is the supported execution API."""
        if action is Action.RESTART_TRANSCODE_WORKER:
            if target != "transcode-a":
                raise ValueError("restart target is not supported by the deterministic demo")
            state = self._replace(transcode_a_health="DEGRADED", sla_at_risk=True)
            return state, ("transcode-a restarted", "sla remains at risk")

        if action is Action.REROUTE_TRANSCODE_WORKLOAD:
            if target != "transcode-b":
                raise ValueError("reroute target is not supported by the deterministic demo")
            state = self._replace(
                active_worker="transcode-b",
                sla_at_risk=False,
                latest_transform_seq=self._state.latest_transform_seq + 1,
            )
            return state, ("workload rerouted to transcode-b", "transcode capacity recovered", "fresh qc still required")

        if action is Action.DISABLE_QUALITY_CONTROL_VALIDATION:
            state = self._replace(qc_validation_enabled=False)
            return state, ("qc validation disabled",)

        raise ValueError(f"unsupported action: {action}")
