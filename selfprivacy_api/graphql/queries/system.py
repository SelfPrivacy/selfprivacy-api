"""Common system information and settings"""

# pylint: disable=too-few-public-methods

import gettext

import strawberry
from opentelemetry import trace
from strawberry.types import Info

import selfprivacy_api.actions.otel as otel_actions
import selfprivacy_api.actions.ssh as ssh_actions
import selfprivacy_api.actions.system as system_actions
from selfprivacy_api.graphql.common_types.dns import DnsRecord
from selfprivacy_api.graphql.common_types.system import (
    UpdateChannel,
    channel_to_graphql,
)
from selfprivacy_api.graphql.queries.common import Alert, Severity
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider
from selfprivacy_api.jobs import Jobs
from selfprivacy_api.jobs.migrate_to_binds import is_bind_migrated
from selfprivacy_api.models.otel import UserDataOpenTelemetrySettings
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.update_channels import UPDATE_CHANNELS, find_update_channel
from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.utils.localization import TranslateSystemMessage as t, get_locale

tracer = trace.get_tracer(__name__)

_ = gettext.gettext


@strawberry.type
class SystemDomainInfo:
    """Information about the system domain"""

    domain: str
    hostname: str
    provider: DnsProvider

    @strawberry.field
    async def required_dns_records(self) -> list[DnsRecord]:
        """Collect all required DNS records for all services"""
        with tracer.start_as_current_span("SystemDomainInfo.required_dns_records"):
            return [
                DnsRecord(
                    record_type=record.type,
                    name=record.name,
                    content=record.content,
                    ttl=record.ttl,
                    priority=record.priority,
                    display_name=record.display_name,
                )
                for record in await ServiceManager.get_all_required_dns_records()
            ]


@tracer.start_as_current_span("get_system_domain_info")
async def get_system_domain_info() -> SystemDomainInfo:
    """Get basic system domain info"""
    with ReadUserData() as user_data:
        return SystemDomainInfo(
            domain=user_data["domain"],
            hostname=user_data["hostname"],
            provider=user_data["dns"]["provider"],
        )


@strawberry.type
class AutoUpgradeOptions:
    """Automatic upgrade options"""

    enable: bool
    allow_reboot: bool


@strawberry.experimental.pydantic.type(model=UserDataOpenTelemetrySettings)
class OpenTelemetrySettings:
    """Server OpenTelemetry settings."""

    enable: strawberry.auto
    endpoint: strawberry.auto
    upload_system_logs: strawberry.auto
    upload_system_metrics: strawberry.auto
    header_names: list[str]
    memory_tracing_enabled: strawberry.auto


def open_telemetry_settings_to_graphql(
    settings: UserDataOpenTelemetrySettings,
) -> OpenTelemetrySettings:
    return OpenTelemetrySettings.from_pydantic(
        settings,
        extra={"header_names": sorted(settings.headers)},
    )


@tracer.start_as_current_span("get_open_telemetry_settings")
async def get_open_telemetry_settings() -> OpenTelemetrySettings:
    """Get server OpenTelemetry settings."""
    return open_telemetry_settings_to_graphql(
        otel_actions.get_open_telemetry_settings()
    )


@tracer.start_as_current_span("get_auto_upgrade_options")
async def get_auto_upgrade_options() -> AutoUpgradeOptions:
    """Get automatic upgrade options"""
    settings = system_actions.get_auto_upgrade_settings()
    return AutoUpgradeOptions(
        enable=settings.enable,
        allow_reboot=settings.allowReboot,
    )


@strawberry.type
class SshSettings:
    """SSH settings and root SSH keys"""

    enable: bool
    password_authentication: bool = strawberry.field(
        deprecation_reason="For security reasons, password authentication is no longer supported. Please use SSH keys."
    )
    root_ssh_keys: list[str]


@tracer.start_as_current_span("get_ssh_settings")
async def get_ssh_settings() -> SshSettings:
    """Get SSH settings"""
    settings = ssh_actions.get_ssh_settings()
    return SshSettings(
        enable=settings.enable,
        password_authentication=False,
        root_ssh_keys=settings.rootKeys,
    )


@tracer.start_as_current_span("get_system_timezone")
async def get_system_timezone() -> str:
    """Get system timezone"""
    return system_actions.get_timezone()


@strawberry.type
class SystemSettings:
    """Common system settings"""

    auto_upgrade: AutoUpgradeOptions = strawberry.field(
        resolver=get_auto_upgrade_options
    )
    open_telemetry: OpenTelemetrySettings = strawberry.field(
        resolver=get_open_telemetry_settings
    )
    ssh: SshSettings = strawberry.field(resolver=get_ssh_settings)
    timezone: str = strawberry.field(resolver=get_system_timezone)


@tracer.start_as_current_span("get_system_version")
async def get_system_version() -> str:
    """Get system version"""
    return system_actions.get_system_version()


@tracer.start_as_current_span("get_python_version")
async def get_python_version() -> str:
    """Get Python version"""
    return system_actions.get_python_version()


@strawberry.type
class SystemInfo:
    """System components versions"""

    system_version: str = strawberry.field(resolver=get_system_version)
    python_version: str = strawberry.field(resolver=get_python_version)

    @strawberry.field
    async def using_binds(self) -> bool:
        """Check if the system is using BINDs"""
        with tracer.start_as_current_span("SystemInfo.using_binds"):
            return is_bind_migrated()


@strawberry.type
class SystemProviderInfo:
    """Information about the VPS/Dedicated server provider"""

    provider: ServerProvider
    id: str


@tracer.start_as_current_span("get_system_provider_info")
async def get_system_provider_info() -> SystemProviderInfo:
    """Get system provider info"""
    with ReadUserData() as user_data:
        return SystemProviderInfo(
            provider=user_data["server"]["provider"],
            id="UNKNOWN",
        )


@tracer.start_as_current_span("get_current_update_channel")
async def get_current_update_channel(info: Info) -> UpdateChannel:
    """Get the update channel the system currently follows"""
    locale = get_locale(info)

    async with FlakeServiceManager() as flake_manager:
        current_url = flake_manager.nixos_config

        definition = find_update_channel(current_url)
        if definition is not None:
            return channel_to_graphql(definition, locale)

        return UpdateChannel(
            id="custom",
            update_url=current_url,
            name=current_url,
            description=t.translate(text=_("Custom update channel"), locale=locale),
        )


@strawberry.type
class SystemUpdatesInfo:
    """Information about current update channel and available update channels"""

    current_channel: UpdateChannel = strawberry.field(
        resolver=get_current_update_channel
    )

    @strawberry.field
    async def channels(self, info: Info) -> list[UpdateChannel]:
        locale = get_locale(info)
        return [
            channel_to_graphql(definition, locale) for definition in UPDATE_CHANNELS
        ]


@strawberry.type
class System:
    """
    Base system type which represents common system status
    """

    status: Alert = strawberry.field(
        resolver=lambda: Alert(
            severity=Severity.INFO,
            title="Test message",
            message="Test message",
            timestamp=None,
        )
    )
    domain_info: SystemDomainInfo = strawberry.field(resolver=get_system_domain_info)
    settings: SystemSettings = strawberry.field(default_factory=SystemSettings)
    info: SystemInfo = strawberry.field(default_factory=SystemInfo)
    updates: SystemUpdatesInfo = strawberry.field(default_factory=SystemUpdatesInfo)
    provider: SystemProviderInfo = strawberry.field(resolver=get_system_provider_info)

    @strawberry.field
    async def busy(self) -> bool:
        """Check if the system is busy"""
        with tracer.start_as_current_span("System.busy"):
            return Jobs.is_busy()
