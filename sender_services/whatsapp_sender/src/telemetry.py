"""OpenTelemetry: traces, metrics and logs sent over OTLP to the collector.

Off unless OTEL_EXPORTER_OTLP_ENDPOINT is set, so the tests and a run without
the collector behave as before. The exporters read the standard OTEL_*
variables (see docker-compose.yml). The rest of the code only uses the
opentelemetry API, which does nothing until this has run.
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_NAME = "whatsapp-sender"


def setup() -> None:
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return

    resource = Resource.create(
        {"service.name": os.getenv("OTEL_SERVICE_NAME", SERVICE_NAME)}
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    metrics.set_meter_provider(
        MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
        )
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)
    # On the root logger, next to the console handler: every log line also goes
    # to Loki, carrying the id of the trace it was written in.
    logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))

    # Every call to the backend and to WAHA becomes a span, and the backend
    # continues the same trace from the traceparent header.
    RequestsInstrumentor().instrument()
