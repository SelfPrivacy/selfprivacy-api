"""Actions for server OpenTelemetry settings."""

import tracemalloc

from opentelemetry import trace

from selfprivacy_api.models.otel import UserDataOpenTelemetrySettings
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.otel import (
    normalize_header_updates,
    normalize_headers,
    validate_endpoint,
)

tracer = trace.get_tracer(__name__)


def _open_telemetry_settings_from_userdata(
    user_data: dict,
) -> UserDataOpenTelemetrySettings:
    telemetry = user_data.get("telemetry", {})
    if not isinstance(telemetry, dict):
        raise ValueError("OpenTelemetry settings must be a JSON object.")

    headers = telemetry.get("headers", {})
    if not isinstance(headers, dict):
        raise ValueError("OpenTelemetry headers must be a JSON object.")

    return UserDataOpenTelemetrySettings(
        enable=telemetry.get("enable", False),
        endpoint=telemetry.get("endpoint"),
        upload_system_logs=telemetry.get("uploadSystemLogs", True),
        upload_system_metrics=telemetry.get("uploadSystemMetrics", True),
        headers=normalize_headers(headers),
        memory_tracing_enabled=tracemalloc.is_tracing(),
    )


@tracer.start_as_current_span("get_open_telemetry_settings")
def get_open_telemetry_settings() -> UserDataOpenTelemetrySettings:
    """Read OpenTelemetry settings and active memory-tracing state."""
    with ReadUserData() as user_data:
        return _open_telemetry_settings_from_userdata(user_data)


@tracer.start_as_current_span("set_open_telemetry_settings")
def set_open_telemetry_settings(
    *,
    enable: bool,
    endpoint: str | None,
    upload_system_logs: bool,
    upload_system_metrics: bool,
    header_updates: list[tuple[str, str | None]] | None = None,
) -> UserDataOpenTelemetrySettings:
    """Replace OpenTelemetry settings and apply header updates atomically."""
    endpoint = validate_endpoint(endpoint, enable)
    normalized_updates = normalize_header_updates(header_updates or [])

    with WriteUserData() as user_data:
        telemetry = user_data.get("telemetry", {})
        if not isinstance(telemetry, dict):
            raise ValueError("OpenTelemetry settings must be a JSON object.")

        headers = telemetry.get("headers", {})
        if not isinstance(headers, dict):
            raise ValueError("OpenTelemetry headers must be a JSON object.")
        normalized_headers = normalize_headers(headers)

        for name, value in normalized_updates:
            if value is None:
                normalized_headers.pop(name, None)
            else:
                normalized_headers[name] = value

        telemetry.update(
            {
                "enable": enable,
                "endpoint": endpoint,
                "uploadSystemLogs": upload_system_logs,
                "uploadSystemMetrics": upload_system_metrics,
                "headers": normalized_headers,
            }
        )
        user_data["telemetry"] = telemetry

        return _open_telemetry_settings_from_userdata(user_data)
