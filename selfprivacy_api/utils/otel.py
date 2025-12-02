import os

OTEL_ENABLED = os.environ.get("SP_API_OTEL_ENABLED") == "1"


def setup_instrumentation():
    if not OTEL_ENABLED:
        return

    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.threading import ThreadingInstrumentor

    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    ThreadingInstrumentor().instrument()
