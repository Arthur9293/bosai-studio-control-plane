from __future__ import annotations

import json

from .telemetry import PipelineTelemetry, TelemetryEvent


def emit_grafana_smoke_scenario(telemetry: PipelineTelemetry) -> dict[str, object]:
    events = (
        TelemetryEvent(
            event="TRANSCODE_A_CODEC_INIT_TIMEOUT",
            stage="TRANSCODE",
            worker="transcode-a",
            sla_at_risk=True,
            transcode_latency_ms=9_800.0,
        ),
        TelemetryEvent(
            event="TRANSCODE_A_RESTARTED_DEGRADED",
            stage="TRANSCODE",
            worker="transcode-a",
            sla_at_risk=True,
            transcode_latency_ms=6_200.0,
        ),
        TelemetryEvent(
            event="WORKLOAD_REROUTED_TO_HEALTHY_CAPACITY",
            stage="TRANSCODE",
            worker="transcode-b",
            sla_at_risk=False,
            transcode_latency_ms=1_450.0,
        ),
        TelemetryEvent(
            event="QC_REQUIRED_AFTER_LATEST_TRANSFORM",
            stage="QUALITY_CONTROL",
            worker="qc-worker",
            sla_at_risk=False,
        ),
    )
    for event in events:
        telemetry.record(event)
    flushed = telemetry.force_flush()
    return {
        "service_name": "bosai-studio-media-pipeline",
        "synthetic": True,
        "events_emitted": [event.event for event in events],
        "force_flush": flushed,
    }


def main() -> None:
    telemetry = PipelineTelemetry.from_otlp_env()
    try:
        print(json.dumps(emit_grafana_smoke_scenario(telemetry), indent=2, sort_keys=True))
    finally:
        telemetry.shutdown()


if __name__ == "__main__":
    main()
