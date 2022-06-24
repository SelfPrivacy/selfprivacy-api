import typing
import strawberry

from selfprivacy_api.graphql.queries.common import Alert
from selfprivacy_api.graphql.queries.providers import DnsProvider, ServerProvider

@strawberry.type
class DnsRecord:
    recordType: str
    name: str
    content: str
    ttl: int
    priority: typing.Optional[int]

@strawberry.type
class SystemDomainInfo:
    domain: str
    hostname: str
    provider: DnsProvider
    required_dns_records: typing.List[DnsRecord]

@strawberry.type
class AutoUpgradeOptions:
    enable: bool
    allow_reboot: bool

@strawberry.type
class SshSettings:
    enable: bool
    password_authentication: bool
    root_ssh_keys: typing.List[str]

@strawberry.type
class SystemSettings:
    auto_upgrade: AutoUpgradeOptions
    ssh: SshSettings
    timezone: str

@strawberry.type
class SystemInfo:
    system_version: str
    python_version: str

@strawberry.type
class SystemProviderInfo:
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