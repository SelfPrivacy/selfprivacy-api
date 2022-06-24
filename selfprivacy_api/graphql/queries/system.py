"""Common system information and settings"""
# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.queries.common import Alert
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider

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

@strawberry.type
class AutoUpgradeOptions:
    """Automatic upgrade options"""
    enable: bool
    allow_reboot: bool

@strawberry.type
class SshSettings:
    """SSH settings and root SSH keys"""
    enable: bool
    password_authentication: bool
    root_ssh_keys: typing.List[str]

@strawberry.type
class SystemSettings:
    """Common system settings"""
    auto_upgrade: AutoUpgradeOptions
    ssh: SshSettings
    timezone: str

@strawberry.type
class SystemInfo:
    """System components versions"""
    system_version: str
    python_version: str

@strawberry.type
class SystemProviderInfo:
    """Information about the VPS/Dedicated server provider"""
    provider: ServerProvider
    id: str

@strawberry.type
class System:
    """
    Base system type which represents common system status
    """
    status: Alert
    domain: SystemDomainInfo
    settings: SystemSettings
    info: SystemInfo
    provider: SystemProviderInfo
    busy: bool
