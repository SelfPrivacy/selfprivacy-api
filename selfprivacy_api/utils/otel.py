import ipaddress
import os
import re
from collections.abc import Sequence
from urllib.parse import urlsplit

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import (
    SpanExporter,
    SpanExportResult,
)

OTEL_ENABLED = os.environ.get("SP_API_OTEL_ENABLED") == "1"

_HEADER_NAME_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_HOST_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def _is_valid_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    hostname = host.rstrip(".")
    return (
        bool(hostname)
        and len(hostname) <= 253
        and all(_HOST_LABEL_PATTERN.fullmatch(label) for label in hostname.split("."))
    )


def validate_endpoint(endpoint: str | None, enable: bool) -> str | None:
    if endpoint is None:
        if enable:
            raise ValueError("OpenTelemetry requires an endpoint when it is enabled.")
        return None

    parsed = urlsplit(endpoint)
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("OpenTelemetry endpoint has an invalid port.") from error

    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or not _is_valid_host(parsed.hostname)
        or port is None
    ):
        raise ValueError(
            "OpenTelemetry endpoint must use https:// and include an explicit port."
        )
    if not 1 <= port <= 65535:
        raise ValueError("OpenTelemetry endpoint has an invalid port.")
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "OpenTelemetry endpoint must not contain user information, a path, a query, or a fragment."
        )

    return f"https://{parsed.netloc}"


def validate_header_name(name: str) -> str:
    if not _HEADER_NAME_PATTERN.fullmatch(name):
        raise ValueError(f"Invalid OpenTelemetry header name: {name}")
    return name.lower()


def validate_header_value(value: str) -> None:
    if any(
        (ord(character) < 32 and character != "\t") or ord(character) == 127
        for character in value
    ):
        raise ValueError(
            "OpenTelemetry header values must not contain control characters."
        )


def normalize_headers(headers: dict) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError(
                "OpenTelemetry headers must contain string names and values."
            )
        normalized_name = validate_header_name(name)
        if normalized_name in normalized:
            raise ValueError(f"Duplicate OpenTelemetry header name: {normalized_name}")
        validate_header_value(value)
        normalized[normalized_name] = value
    return normalized


def normalize_header_updates(
    header_updates: list[tuple[str, str | None]],
) -> list[tuple[str, str | None]]:
    normalized: list[tuple[str, str | None]] = []
    updated_names: set[str] = set()
    for name, value in header_updates:
        normalized_name = validate_header_name(name)
        if normalized_name in updated_names:
            raise ValueError(f"Duplicate OpenTelemetry header name: {normalized_name}")
        if value is not None:
            validate_header_value(value)
        normalized.append((normalized_name, value))
        updated_names.add(normalized_name)
    return normalized


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
