from __future__ import annotations

from dataclasses import dataclass
import os

from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


SERVICE_NAME = "bosai-studio-media-pipeline"
SERVICE_NAMESPACE = "bosai-studio-control-plane"
SYNTHETIC_SCENARIO = "agentic-cinema-grafana-track"


@dataclass(frozen=True)
class TelemetryEvent:
    event: str
    stage: str
    worker: str
    sla_at_risk: bool
    incident_type: str = "TRANSCODE_A_CODEC_INIT_TIMEOUT"
    transcode_latency_ms: float | None = None
    run_id: str | None = None


class PipelineTelemetry:
    """OpenTelemetry instrumentation for the explicitly synthetic media pipeline.

    OTLP exporters intentionally read standard OpenTelemetry environment variables.
    No Grafana credential is accepted as a function argument or stored in application state.
    """

    def __init__(
        self,
        *,
        tracer_provider: TracerProvider,
        meter_provider: MeterProvider,
        logger_provider: LoggerProvider,
    ) -> None:
        self._tracer_provider = tracer_provider
        self._meter_provider = meter_provider
        self._logger_provider = logger_provider
        self.tracer = tracer_provider.get_tracer(SERVICE_NAMESPACE)
        self.meter = meter_provider.get_meter(SERVICE_NAMESPACE)
        self.pipeline_events = self.meter.create_counter(
            "bosai_studio_pipeline_events",
            unit="1",
            description="Synthetic BOSAI Studio media pipeline state-transition events.",
        )
        self.transcode_latency = self.meter.create_histogram(
            "bosai_studio_transcode_latency_ms",
            unit="ms",
            description="Synthetic trailer transcode latency observed by the demo pipeline.",
        )
        self.logger = logger_provider.get_logger(SERVICE_NAMESPACE)

    @staticmethod
    def resource() -> Resource:
        return Resource.create(
            {
                "service.name": SERVICE_NAME,
                "service.namespace": SERVICE_NAMESPACE,
                "deployment.environment.name": "hackathon",
                "bosai.synthetic": True,
                "bosai.scenario": SYNTHETIC_SCENARIO,
            }
        )

    @classmethod
    def from_otlp_env(cls) -> "PipelineTelemetry":
        """Build HTTP/protobuf OTLP exporters from standard OTEL_* environment variables.

        Grafana Cloud's generated connection variables should provide at minimum:
        OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf, and
        OTEL_EXPORTER_OTLP_HEADERS. This method fails closed when no endpoint exists.
        """
        if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            raise RuntimeError("OTEL_EXPORTER_OTLP_ENDPOINT is required for real telemetry export")

        resource = cls.resource()

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(),
            export_interval_millis=1_000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))

        return cls(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            logger_provider=logger_provider,
        )

    def record(self, event: TelemetryEvent) -> None:
        attributes: dict[str, str | bool] = {
            "bosai.event": event.event,
            "bosai.pipeline.stage": event.stage,
            "bosai.worker": event.worker,
            "bosai.sla_at_risk": event.sla_at_risk,
            "bosai.incident.type": event.incident_type,
            "bosai.synthetic": True,
        }
        if event.run_id:
            attributes["bosai.run_id"] = event.run_id

        self.pipeline_events.add(1, attributes=attributes)
        if event.transcode_latency_ms is not None:
            self.transcode_latency.record(event.transcode_latency_ms, attributes=attributes)

        with self.tracer.start_as_current_span(f"pipeline.{event.event.lower()}") as span:
            for key, value in attributes.items():
                span.set_attribute(key, value)
            if event.transcode_latency_ms is not None:
                span.set_attribute("bosai.transcode.latency_ms", event.transcode_latency_ms)

            run_fragment = f" run_id={event.run_id}" if event.run_id else ""
            self.logger.emit(
                severity_text="INFO",
                body=(
                    f"{event.event} stage={event.stage} worker={event.worker} "
                    f"sla_at_risk={str(event.sla_at_risk).lower()} synthetic=true{run_fragment}"
                ),
                attributes=attributes,
            )

    def force_flush(self, timeout_millis: int = 10_000) -> bool:
        results = [
            self._tracer_provider.force_flush(timeout_millis=timeout_millis),
            self._meter_provider.force_flush(timeout_millis=timeout_millis),
            self._logger_provider.force_flush(timeout_millis=timeout_millis),
        ]
        return all(result is not False for result in results)

    def shutdown(self) -> None:
        self._logger_provider.shutdown()
        self._meter_provider.shutdown()
        self._tracer_provider.shutdown()
