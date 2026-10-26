"""OpenTelemetry: traces, metrics and logs sent over OTLP to the collector.

Off unless OTEL_EXPORTER_OTLP_ENDPOINT is set, so the tests and a local run
without the collector behave as before. The exporters read the standard
OTEL_* variables (see docker-compose.yml). The rest of the code only uses the
opentelemetry API, which does nothing until this has run.
"""

import logging
import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.engine import Engine

SERVICE_NAME = "backend"


def setup(app: FastAPI, engine: Engine) -> None:
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
    _setup_logging(logger_provider)

    # Request spans and the http.server.* metrics. A worker's call carries a
    # traceparent header, so its trace continues here. The ASGI receive/send
    # spans only repeat the request span, so they are left out.
    FastAPIInstrumentor.instrument_app(app, exclude_spans=["receive", "send"])
    # Every query becomes a span under the request that ran it.
    SQLAlchemyInstrumentor().instrument(engine=engine)


def _setup_logging(logger_provider: LoggerProvider) -> None:
    root = logging.getLogger()
    # uvicorn only configures its own loggers, so the app's ones fell through
    # to a root at WARNING with no handler and their info lines were lost.
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Every log line also goes to Loki, carrying the id of its trace.
    root.addHandler(LoggingHandler(logger_provider=logger_provider))

    # echo=True prints every statement through its own handler. They are
    # already in the traces as spans, so they stay out of Loki.
    logging.getLogger("sqlalchemy.engine.Engine").propagate = False
