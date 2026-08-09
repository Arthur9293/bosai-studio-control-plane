from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from bosai_studio.telemetry import PipelineTelemetry, SERVICE_NAME, TelemetryEvent


class TelemetryContractTests(unittest.TestCase):
    def test_resource_marks_workload_synthetic_and_names_service(self) -> None:
        attributes = PipelineTelemetry.resource().attributes
        self.assertEqual(attributes["service.name"], SERVICE_NAME)
        self.assertTrue(attributes["bosai.synthetic"])
        self.assertEqual(attributes["deployment.environment.name"], "hackathon")

    def test_real_export_fails_closed_without_otlp_endpoint(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OTEL_EXPORTER_OTLP_ENDPOINT"):
                PipelineTelemetry.from_otlp_env()

    def test_event_contract_is_low_cardinality_and_explicitly_synthetic(self) -> None:
        event = TelemetryEvent(
            event="TRANSCODE_A_CODEC_INIT_TIMEOUT",
            stage="TRANSCODE",
            worker="transcode-a",
            sla_at_risk=True,
            transcode_latency_ms=9800.0,
        )
        self.assertEqual(event.incident_type, "TRANSCODE_A_CODEC_INIT_TIMEOUT")
        self.assertEqual(event.stage, "TRANSCODE")
        self.assertEqual(event.worker, "transcode-a")
        self.assertTrue(event.sla_at_risk)


class TelemetryEmissionTests(unittest.TestCase):
    def test_record_emits_trace_metric_and_log_without_network(self) -> None:
        resource = PipelineTelemetry.resource()
        span_exporter = InMemorySpanExporter()
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

        metric_reader = InMemoryMetricReader()
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

        log_exporter = InMemoryLogRecordExporter()
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))

        telemetry = PipelineTelemetry(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            logger_provider=logger_provider,
        )
        telemetry.record(
            TelemetryEvent(
                event="TRANSCODE_A_CODEC_INIT_TIMEOUT",
                stage="TRANSCODE",
                worker="transcode-a",
                sla_at_risk=True,
                transcode_latency_ms=9800.0,
            )
        )

        self.assertEqual(len(span_exporter.get_finished_spans()), 1)
        self.assertIsNotNone(metric_reader.get_metrics_data())
        self.assertGreaterEqual(len(log_exporter.get_finished_logs()), 1)


if __name__ == "__main__":
    unittest.main()
