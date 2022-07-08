"""Common system information and settings"""
# pylint: disable=too-few-public-methods
import subprocess
import typing
import strawberry

from selfprivacy_api.graphql.queries.common import Alert, Severity
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider
from selfprivacy_api.utils import ReadUserData


@strawberry.type
class DnsRecord:
    """DNS record"""

    recordType: str
    name: str
    content: str
    ttl: int
    priority: typing.Optional[int]


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
    with ReadUserData() as user_data:
        if "autoUpgrade" not in user_data:
            return AutoUpgradeOptions(enable=True, allow_reboot=False)
        if "enable" not in user_data["autoUpgrade"]:
            user_data["autoUpgrade"]["enable"] = True
        if "allowReboot" not in user_data["autoUpgrade"]:
            user_data["autoUpgrade"]["allowReboot"] = False
        return AutoUpgradeOptions(
            enable=user_data["autoUpgrade"]["enable"],
            allow_reboot=user_data["autoUpgrade"]["allowReboot"],
        )


@strawberry.type
class SshSettings:
    """SSH settings and root SSH keys"""

    enable: bool
    password_authentication: bool
    root_ssh_keys: typing.List[str]


def get_ssh_settings() -> SshSettings:
    """Get SSH settings"""
    with ReadUserData() as user_data:
        if "ssh" not in user_data:
            return SshSettings(
                enable=False, password_authentication=False, root_ssh_keys=[]
            )
        if "enable" not in user_data["ssh"]:
            user_data["ssh"]["enable"] = False
        if "passwordAuthentication" not in user_data["ssh"]:
            user_data["ssh"]["passwordAuthentication"] = False
        if "rootKeys" not in user_data["ssh"]:
            user_data["ssh"]["rootKeys"] = []
        return SshSettings(
            enable=user_data["ssh"]["enable"],
            password_authentication=user_data["ssh"]["passwordAuthentication"],
            root_ssh_keys=user_data["ssh"]["rootKeys"],
        )


def get_system_timezone() -> str:
    """Get system timezone"""
    with ReadUserData() as user_data:
        if "timezone" not in user_data:
            return "Europe/Uzhgorod"
        return user_data["timezone"]


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
    return subprocess.check_output(["uname", "-a"]).decode("utf-8").strip()


def get_python_version() -> str:
    """Get Python version"""
    return subprocess.check_output(["python", "-V"]).decode("utf-8").strip()


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
