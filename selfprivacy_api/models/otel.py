"""OpenTelemetry data models."""

from pydantic import BaseModel, Field


class UserDataOpenTelemetrySettings(BaseModel):
    """OpenTelemetry settings stored in userdata.json."""

    enable: bool = False
    endpoint: str | None = None
    upload_system_logs: bool = True
    upload_system_metrics: bool = True
    headers: dict[str, str] = Field(default_factory=dict)
    memory_tracing_enabled: bool = False
