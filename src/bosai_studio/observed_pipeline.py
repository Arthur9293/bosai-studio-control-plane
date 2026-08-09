from __future__ import annotations

from .contracts import Action
from .pipeline import MediaPipelineSim, PipelineState
from .telemetry import PipelineTelemetry, TelemetryEvent


class ObservedMediaPipelineSim(MediaPipelineSim):
    """Phase 3 synthetic pipeline with Phase 4 OpenTelemetry observations."""

    def __init__(self, telemetry: PipelineTelemetry, state: PipelineState | None = None) -> None:
        super().__init__(state)
        self.telemetry = telemetry

    def emit_initial_incident(self) -> None:
        state = self.snapshot()
        self.telemetry.record(
            TelemetryEvent(
                event="TRANSCODE_A_CODEC_INIT_TIMEOUT",
                stage="TRANSCODE",
                worker="transcode-a",
                sla_at_risk=state.sla_at_risk,
                transcode_latency_ms=9_800.0,
            )
        )

    def _execute_authorized(self, action: Action, target: str) -> tuple[PipelineState, tuple[str, ...]]:
        state, postconditions = super()._execute_authorized(action, target)

        if action is Action.RESTART_TRANSCODE_WORKER:
            self.telemetry.record(
                TelemetryEvent(
                    event="TRANSCODE_A_RESTARTED_DEGRADED",
                    stage="TRANSCODE",
                    worker="transcode-a",
                    sla_at_risk=state.sla_at_risk,
                    transcode_latency_ms=6_200.0,
                )
            )

        elif action is Action.REROUTE_TRANSCODE_WORKLOAD:
            self.telemetry.record(
                TelemetryEvent(
                    event="WORKLOAD_REROUTED_TO_HEALTHY_CAPACITY",
                    stage="TRANSCODE",
                    worker="transcode-b",
                    sla_at_risk=state.sla_at_risk,
                    transcode_latency_ms=1_450.0,
                )
            )
            if not state.fresh_qc_pass:
                self.telemetry.record(
                    TelemetryEvent(
                        event="QC_REQUIRED_AFTER_LATEST_TRANSFORM",
                        stage="QUALITY_CONTROL",
                        worker="qc-worker",
                        sla_at_risk=state.sla_at_risk,
                    )
                )

        elif action is Action.DISABLE_QUALITY_CONTROL_VALIDATION:
            self.telemetry.record(
                TelemetryEvent(
                    event="QC_VALIDATION_DISABLED",
                    stage="QUALITY_CONTROL",
                    worker="qc-worker",
                    sla_at_risk=state.sla_at_risk,
                )
            )

        return state, postconditions
