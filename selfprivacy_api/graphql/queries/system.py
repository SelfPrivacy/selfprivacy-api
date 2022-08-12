"""Common system information and settings"""
# pylint: disable=too-few-public-methods
import os
import typing
import strawberry
from selfprivacy_api.graphql.common_types.dns import DnsRecord

from selfprivacy_api.graphql.queries.common import Alert, Severity
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider
from selfprivacy_api.utils import ReadUserData
import selfprivacy_api.actions.system as system_actions
import selfprivacy_api.actions.ssh as ssh_actions


@strawberry.type
class SystemDomainInfo:
    """Information about the system domain"""

    domain: str
    hostname: str
    provider: DnsProvider
    required_dns_records: typing.List[DnsRecord]


def get_system_domain_info() -> SystemDomainInfo:
    """Get basic system domain info"""
    with ReadUserData() as user_data:
        return SystemDomainInfo(
            domain=user_data["domain"],
            hostname=user_data["hostname"],
            provider=DnsProvider.CLOUDFLARE,
            # TODO: get ip somehow
            required_dns_records=[],
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
    password_authentication: bool
    root_ssh_keys: typing.List[str]


def get_ssh_settings() -> SshSettings:
    """Get SSH settings"""
    settings = ssh_actions.get_ssh_settings()
    return SshSettings(
        enable=settings.enable,
        password_authentication=settings.passwordAuthentication,
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


@strawberry.type
class SystemProviderInfo:
    """Information about the VPS/Dedicated server provider"""

    provider: ServerProvider
    id: str


def get_system_provider_info() -> SystemProviderInfo:
    """Get system provider info"""
    return SystemProviderInfo(provider=ServerProvider.HETZNER, id="UNKNOWN")


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
    settings: SystemSettings = SystemSettings()
    info: SystemInfo = SystemInfo()
    provider: SystemProviderInfo = strawberry.field(resolver=get_system_provider_info)
    busy: bool = False

    @strawberry.field
    def working_directory(self) -> str:
        """Get working directory"""
        return os.getcwd()
