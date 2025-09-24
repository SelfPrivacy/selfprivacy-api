from enum import Enum
from typing import Optional, List
import datetime
import strawberry
from opentelemetry import trace
import anyio

from selfprivacy_api.graphql.common_types.backup import BackupReason
from selfprivacy_api.graphql.common_types.dns import DnsRecord

from selfprivacy_api.models.services import License
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services import Service as ServiceInterface
from selfprivacy_api.services import ServiceDnsRecord

from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.utils.network import get_ip4, get_ip6

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("get_usages")
def get_usages(root: "StorageVolume") -> list["StorageUsageInterface"]:
    """Get usages of a volume"""
    return [
        ServiceStorageUsage(
            service=service_to_graphql_service(service),
            title=service.get_display_name(),
            used_space=str(service.get_storage_usage()),
            volume=get_volume_by_id(service.get_drive()),
        )
        for service in ServiceManager.get_services_by_location(root.name)
    ]


@strawberry.type
class StorageVolume:
    """Stats and basic info about a volume or a system disk."""

    total_space: str
    free_space: str
    used_space: str
    root: bool
    name: str
    model: Optional[str]
    serial: Optional[str]
    type: str

    @strawberry.field
    def usages(self) -> list["StorageUsageInterface"]:
        """Get usages of a volume"""
        return get_usages(self)


@strawberry.interface
class StorageUsageInterface:
    used_space: str
    volume: Optional[StorageVolume]
    title: str


@strawberry.type
class ServiceStorageUsage(StorageUsageInterface):
    """Storage usage for a service"""

    service: Optional["Service"]


@strawberry.enum
class ServiceStatusEnum(Enum):
    ACTIVE = "ACTIVE"
    RELOADING = "RELOADING"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ACTIVATING = "ACTIVATING"
    DEACTIVATING = "DEACTIVATING"
    OFF = "OFF"


@strawberry.enum
class SupportLevelEnum(Enum):
    """Enum representing the support level of a service."""

    NORMAL = "normal"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


@strawberry.experimental.pydantic.type(model=License)
class LicenseType:
    free: strawberry.auto
    full_name: strawberry.auto
    redistributable: strawberry.auto
    short_name: strawberry.auto
    spdx_id: strawberry.auto
    url: strawberry.auto
    deprecated: strawberry.auto


@tracer.start_as_current_span("get_storage_usage")
async def get_storage_usage(root: "Service") -> ServiceStorageUsage:
    """Get storage usage for a service"""
    service = await anyio.to_thread.run_sync(ServiceManager.get_service_by_id, root.id)
    if service is None:
        return ServiceStorageUsage(
            service=service,
            title="Not found",
            used_space="0",
            volume=get_volume_by_id("sda1"),
        )
    return ServiceStorageUsage(
        service=service_to_graphql_service(service),
        title=service.get_display_name(),
        used_space=str(service.get_storage_usage()),
        volume=get_volume_by_id(service.get_drive()),
    )


# TODO: This won't be needed when deriving DnsRecord via strawberry pydantic integration
# https://strawberry.rocks/docs/integrations/pydantic
# Remove when the link above says it got stable.
def service_dns_to_graphql(record: ServiceDnsRecord) -> DnsRecord:
    return DnsRecord(
        record_type=record.type,
        name=record.name,
        content=record.content,
        ttl=record.ttl,
        priority=record.priority,
        display_name=record.display_name,
    )


@strawberry.interface
class ConfigItem:
    field_id: str
    description: str
    widget: str
    type: str


@strawberry.type
class StringConfigItem(ConfigItem):
    value: str
    default_value: str
    regex: Optional[str]


@strawberry.type
class BoolConfigItem(ConfigItem):
    value: bool
    default_value: bool


@strawberry.type
class EnumConfigItem(ConfigItem):
    value: str
    default_value: str
    options: list[str]


@tracer.start_as_current_span("config_item_to_graphql")
def config_item_to_graphql(item: dict) -> ConfigItem:
    item_type = item.get("type")
    if item_type == "string":
        return StringConfigItem(
            field_id=item["id"],
            description=item["description"],
            widget=item["widget"],
            type=item_type,
            value=item["value"],
            default_value=item["default_value"],
            regex=item.get("regex"),
        )
    elif item_type == "bool":
        return BoolConfigItem(
            field_id=item["id"],
            description=item["description"],
            widget=item["widget"],
            type=item_type,
            value=item["value"],
            default_value=item["default_value"],
        )
    elif item_type == "enum":
        return EnumConfigItem(
            field_id=item["id"],
            description=item["description"],
            widget=item["widget"],
            type=item_type,
            value=item["value"],
            default_value=item["default_value"],
            options=item["options"],
        )
    else:
        raise ValueError(f"Unknown config item type {item_type}")


@strawberry.type
class Service:
    id: str
    display_name: str
    description: str
    svg_icon: str
    is_movable: bool
    is_required: bool
    is_enabled: bool
    is_installed: bool
    is_system_service: bool
    can_be_backed_up: bool
    backup_description: str
    status: ServiceStatusEnum
    url: Optional[str]
    license: List[LicenseType]
    homepage: Optional[str]
    source_page: Optional[str]
    support_level: SupportLevelEnum

    @strawberry.field
    async def dns_records(self) -> Optional[List[DnsRecord]]:
        with tracer.start_as_current_span(
            "resolve_service_dns_records", attributes={"service_id": self.id}
        ):
            service = await anyio.to_thread.run_sync(
                ServiceManager.get_service_by_id, self.id
            )
            if service is None:
                raise LookupError(f"no service {self.id}. Should be unreachable")

            raw_records = service.get_dns_records(get_ip4(), get_ip6())
            dns_records = [service_dns_to_graphql(record) for record in raw_records]
            return dns_records

    @strawberry.field
    async def storage_usage(self) -> ServiceStorageUsage:
        """Get storage usage for a service"""
        with tracer.start_as_current_span(
            "get_storage_usage", attributes={"service_id": self.id}
        ):
            return await get_storage_usage(self)

    @strawberry.field
    async def configuration(self) -> Optional[List[ConfigItem]]:
        """Get service configuration"""
        with tracer.start_as_current_span(
            "resolve_service_configuration", attributes={"service_id": self.id}
        ):
            service = await anyio.to_thread.run_sync(
                ServiceManager.get_service_by_id, self.id
            )
            if service is None:
                return None
            config_items = service.get_configuration()
            # If it is an empty dict, return none
            if not config_items:
                return None
            # By the "type" field convert every dict into a ConfigItem. In the future there will be more types.
            unsorted_config_items = [config_items[item] for item in config_items]
            # Sort the items by their weight. If there is no weight, implicitly set it to 50.
            config_items = sorted(
                unsorted_config_items, key=lambda x: x.get("weight", 50)
            )
            return [config_item_to_graphql(item) for item in config_items]

    # TODO: fill this
    @strawberry.field
    def backup_snapshots(self) -> Optional[List["SnapshotInfo"]]:
        return None


@strawberry.type
class SnapshotInfo:
    id: str
    service: Service
    created_at: datetime.datetime
    reason: BackupReason


@tracer.start_as_current_span("service_to_graphql_service")
def service_to_graphql_service(service: ServiceInterface) -> Service:
    """Convert service to graphql service"""
    return Service(
        id=service.get_id(),
        display_name=service.get_display_name(),
        description=service.get_description(),
        svg_icon=service.get_svg_icon(),
        is_movable=service.is_movable(),
        is_required=service.is_required(),
        is_enabled=service.is_enabled(),
        is_installed=service.is_installed(),
        can_be_backed_up=service.can_be_backed_up(),
        backup_description=service.get_backup_description(),
        status=ServiceStatusEnum(service.get_status().value),
        url=service.get_url(),
        is_system_service=service.is_system_service(),
        license=[
            LicenseType.from_pydantic(license) for license in service.get_license()
        ],
        homepage=service.get_homepage(),
        source_page=service.get_source_page(),
        support_level=SupportLevelEnum(service.get_support_level().value),
    )


@tracer.start_as_current_span("get_volume_by_id")
def get_volume_by_id(volume_id: str) -> Optional[StorageVolume]:
    """Get volume by id"""
    volume = BlockDevices().get_block_device_by_canonical_name(volume_id)
    if volume is None:
        return None
    return StorageVolume(
        total_space=(
            str(volume.fssize) if volume.fssize is not None else str(volume.size)
        ),
        free_space=str(volume.fsavail),
        used_space=str(volume.fsused),
        root=volume.is_root(),
        name=volume.canonical_name,
        model=volume.model,
        serial=volume.serial,
        type=volume.type,
    )
