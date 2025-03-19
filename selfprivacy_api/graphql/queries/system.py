"""Common system information and settings"""

# pylint: disable=too-few-public-methods
import os
import typing
import strawberry

from selfprivacy_api.graphql.common_types.dns import DnsRecord

from selfprivacy_api.graphql.queries.common import Alert, Severity
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider
from selfprivacy_api.jobs import Jobs
from selfprivacy_api.jobs.migrate_to_binds import is_bind_migrated
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.utils import ReadUserData
import selfprivacy_api.actions.system as system_actions
import selfprivacy_api.actions.ssh as ssh_actions


@strawberry.type
class SystemDomainInfo:
    """Information about the system domain"""

    domain: str
    hostname: str
    provider: DnsProvider

    @strawberry.field
    def required_dns_records(self) -> typing.List[DnsRecord]:
        """Collect all required DNS records for all services"""
        return [
            DnsRecord(
                record_type=record.type,
                name=record.name,
                content=record.content,
                ttl=record.ttl,
                priority=record.priority,
                display_name=record.display_name,
            )
            for record in ServiceManager.get_all_required_dns_records()
        ]


def get_system_domain_info() -> SystemDomainInfo:
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


def get_auto_upgrade_options() -> AutoUpgradeOptions:
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
    root_ssh_keys: typing.List[str]


def get_ssh_settings() -> SshSettings:
    """Get SSH settings"""
    settings = ssh_actions.get_ssh_settings()
    return SshSettings(
        enable=settings.enable,
        password_authentication=False,
        root_ssh_keys=settings.rootKeys,
    )


def get_system_timezone() -> str:
    """Get system timezone"""
    return system_actions.get_timezone()


@strawberry.type
class SystemSettings:
    """Common system settings"""

    auto_upgrade: AutoUpgradeOptions = strawberry.field(
        resolver=get_auto_upgrade_options
    )
    ssh: SshSettings = strawberry.field(resolver=get_ssh_settings)
    timezone: str = strawberry.field(resolver=get_system_timezone)


def get_system_version() -> str:
    """Get system version"""
    return system_actions.get_system_version()


def get_python_version() -> str:
    """Get Python version"""
    return system_actions.get_python_version()


@strawberry.type
class SystemInfo:
    """System components versions"""

    system_version: str = strawberry.field(resolver=get_system_version)
    python_version: str = strawberry.field(resolver=get_python_version)

    @strawberry.field
    def using_binds(self) -> bool:
        """Check if the system is using BINDs"""
        return is_bind_migrated()


@strawberry.type
class SystemProviderInfo:
    """Information about the VPS/Dedicated server provider"""

    provider: ServerProvider
    id: str


def get_system_provider_info() -> SystemProviderInfo:
    """Get system provider info"""
    with ReadUserData() as user_data:
        return SystemProviderInfo(
            provider=user_data["server"]["provider"],
            id="UNKNOWN",
        )


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
    provider: SystemProviderInfo = strawberry.field(resolver=get_system_provider_info)

    @strawberry.field
    def busy(self) -> bool:
        """Check if the system is busy"""
        return Jobs.is_busy()

    @strawberry.field
    def working_directory(self) -> str:
        """Get working directory"""
        return os.getcwd()
