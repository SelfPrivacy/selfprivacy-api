import os
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)

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


class FilteringSpanExporter(SpanExporter):
    def __init__(self, exporter: SpanExporter):
        self.exporter = exporter

    @staticmethod
    def _is_redis_root_span(span: ReadableSpan) -> bool:
        return span.parent is None and (
            span.name.startswith("redis.")
            or span.attributes.get("db.system") == "redis"
        )

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        filtered_spans = [span for span in spans if not self._is_redis_root_span(span)]
        if not filtered_spans:
            return SpanExportResult.SUCCESS
        return self.exporter.export(filtered_spans)

    def shutdown(self) -> None:
        self.exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self.exporter.force_flush(timeout_millis)
