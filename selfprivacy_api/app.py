#!/usr/bin/env python3
"""SelfPrivacy server management API"""
import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from contextlib import asynccontextmanager

from opentelemetry.sdk.resources import (
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_INSTANCE_ID,
    Resource,
)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider, get_logger
from opentelemetry import context as otel_context


import uvicorn
from copy import deepcopy
from uvicorn.config import LOGGING_CONFIG

from selfprivacy_api.dependencies import get_api_version
from selfprivacy_api.graphql.schema import schema
from selfprivacy_api.migrations import run_migrations
from selfprivacy_api.services.suggested import SuggestedServices
from selfprivacy_api.utils.otel import OTEL_ENABLED
from selfprivacy_api.utils.memory_profiler import memory_profiler_task

from starlette.middleware.sessions import SessionMiddleware
from secrets import token_urlsafe

from selfprivacy_api.userpanel.routes.login import router as login_router
from selfprivacy_api.userpanel.routes.user import router as user_router
from selfprivacy_api.userpanel.routes.internal import router as internal_router

from selfprivacy_api.userpanel.static import static_dir


# Capture OTel context per request/WS and expose it to Strawberry resolvers
async def graphql_context_getter():
    return {
        "otel_context": otel_context.get_current(),
    }


if OTEL_ENABLED:
    resource = Resource.create(
        attributes={
            SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "selfprivacy_api"),
            SERVICE_VERSION: get_api_version(),
            SERVICE_INSTANCE_ID: os.getenv(
                "OTEL_SERVICE_INSTANCE_ID", "unknown-instance"
            ),
        }
    )

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

    log_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.basicConfig(handlers=[log_handler], level=logging.INFO)

    # Ensure Uvicorn loggers also emit via OpenTelemetry by supplying a custom log_config
    uvicorn_log_config = deepcopy(LOGGING_CONFIG)
    uvicorn_log_config["handlers"]["otel"] = {
        "class": "opentelemetry.sdk._logs.LoggingHandler",
        "level": "INFO",
        # Pass the already configured logger_provider so the handler exports to OTLP
        "logger_provider": logger_provider,
    }
    for _name in ("uvicorn", "uvicorn.error"):
        if _name in uvicorn_log_config.get("loggers", {}):
            _cfg = uvicorn_log_config["loggers"][_name]
            _handlers = _cfg.setdefault("handlers", [])
            if "otel" not in _handlers:
                _handlers.append("otel")
        else:
            uvicorn_log_config.setdefault("loggers", {})[_name] = {
                "handlers": ["otel"],
                "level": "INFO",
                "propagate": False,
            }
    if "root" in uvicorn_log_config:
        _root = uvicorn_log_config["root"]
        _root_handlers = _root.setdefault("handlers", [])
        if "otel" not in _root_handlers:
            _root_handlers.append("otel")
    else:
        uvicorn_log_config["root"] = {"level": "INFO", "handlers": ["otel"]}

    ThreadingInstrumentor().instrument()

logger = get_logger(__name__)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await run_migrations()
    asyncio.create_task(memory_profiler_task())
    asyncio.create_task(
        SuggestedServices.sync()
    )  # TODO(nhnn): Move it out of app_lifespan to appropriate place.
    try:
        yield
    finally:
        # Flush OpenTelemetry logs/traces on shutdown
        try:
            logger_provider.shutdown()
        except Exception:
            pass
        try:
            tracer_provider.shutdown()
        except Exception:
            pass


app = FastAPI(lifespan=app_lifespan)

graphql_app: GraphQLRouter[dict[str, otel_context.Context], None] = GraphQLRouter(
    schema,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ],
    context_getter=graphql_context_getter,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

secret_key = token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(graphql_app, prefix="/graphql")
app.include_router(login_router, prefix="/login")
app.include_router(user_router, prefix="/user")
app.include_router(internal_router, prefix="/internal")


@app.get("/api/version")
async def get_version():
    """Get the version of the server"""
    return {"version": get_api_version()}


@app.get("/")
async def root():
    return RedirectResponse(url="/user")


if OTEL_ENABLED:
    FastAPIInstrumentor.instrument_app(app)


if __name__ == "__main__":
    uvicorn.run(
        "selfprivacy_api.app:app",
        host="127.0.0.1",
        port=5050,
        log_level="info",
        log_config=uvicorn_log_config if OTEL_ENABLED else None,
    )
