import logging
from os import environ
import os

from selfprivacy_api.dependencies import get_api_version
from selfprivacy_api.utils.huey import huey

from selfprivacy_api.backup.tasks import *
from selfprivacy_api.services.tasks import move_service
from selfprivacy_api.jobs.upgrade_system import rebuild_system_task

from selfprivacy_api.jobs.test import test_job
from selfprivacy_api.jobs.nix_collect_garbage import calculate_and_clear_dead_paths

from opentelemetry.sdk.resources import (
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_INSTANCE_ID,
    Resource,
)

from selfprivacy_api.utils.otel import OTEL_ENABLED, setup_instrumentation
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider, get_logger


setup_instrumentation()

resource = Resource.create(
    attributes={
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "selfprivacy_api_worker"),
        SERVICE_VERSION: get_api_version(),
        SERVICE_INSTANCE_ID: os.getenv("OTEL_SERVICE_INSTANCE_ID", "unknown-instance"),
    }
)

if OTEL_ENABLED:
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    otlp_protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    otlp_insecure = (
        True if "localhost" in otlp_endpoint or "127.0.0.1" in otlp_endpoint else False
    )

    tracer_provider = TracerProvider(resource=resource)
    trace_processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=otlp_endpoint,
            headers=otlp_headers,
            insecure=otlp_insecure,
        )
    )
    tracer_provider.add_span_processor(trace_processor)
    trace.set_tracer_provider(tracer_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=otlp_endpoint,
            headers=otlp_headers,
            insecure=otlp_insecure,
        )
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_processor = BatchLogRecordProcessor(
        OTLPLogExporter(
            endpoint=otlp_endpoint,
            headers=otlp_headers,
            insecure=otlp_insecure,
        )
    )
    logger_provider.add_log_record_processor(logger_processor)
    set_logger_provider(logger_provider)

    logger = get_logger(__name__)

    log_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.basicConfig(handlers=[log_handler], level=logging.INFO)


if environ.get("TEST_MODE"):
    from tests.test_huey import sum
