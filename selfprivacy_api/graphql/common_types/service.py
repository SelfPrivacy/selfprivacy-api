from enum import Enum
import typing
import strawberry
from strawberry.types import Info
from selfprivacy_api.graphql.common_types.dns import DnsRecord
from selfprivacy_api.graphql.common_types.backup_snapshot import SnapshotInfo

from selfprivacy_api.services import get_service_by_id, get_services_by_location
from selfprivacy_api.services import Service as ServiceInterface
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.utils.localization import Localization as L10n


def get_usages(root: "StorageVolume", locale: str) -> list["StorageUsageInterface"]:
    """Get usages of a volume"""
    return [
        ServiceStorageUsage(
            service=service_to_graphql_service(service, locale),
            title=service.get_display_name(),
            used_space=str(service.get_storage_usage()),
            volume=get_volume_by_id(service.get_drive()),
        )
        for service in get_services_by_location(root.name)
    ]


@strawberry.type
class StorageVolume:
    """Stats and basic info about a volume or a system disk."""

    total_space: str
    free_space: str
    used_space: str
    root: bool
    name: str
    model: typing.Optional[str]
    serial: typing.Optional[str]
    type: str

    @strawberry.field
    def usages(self, info: Info) -> list["StorageUsageInterface"]:
        """Get usages of a volume"""
        locale = info.context["locale"]
        return get_usages(self, locale)


@strawberry.interface
class StorageUsageInterface:
    used_space: str
    volume: typing.Optional[StorageVolume]
    title: str


@strawberry.type
class ServiceStorageUsage(StorageUsageInterface):
    """Storage usage for a service"""

    service: typing.Optional["Service"]


@strawberry.enum
class ServiceStatusEnum(Enum):
    ACTIVE = "ACTIVE"
    RELOADING = "RELOADING"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"
    ACTIVATING = "ACTIVATING"
    DEACTIVATING = "DEACTIVATING"
    OFF = "OFF"


def get_storage_usage(root: "Service", locale: str) -> ServiceStorageUsage:
    """Get storage usage for a service"""
    service = get_service_by_id(root.id)
    if service is None:
        return ServiceStorageUsage(
            service=service,
            title="Not found",
            used_space="0",
            volume=get_volume_by_id("sda1"),
        )
    return ServiceStorageUsage(
        service=service_to_graphql_service(service, locale),
        title=service.get_display_name(),
        used_space=str(service.get_storage_usage()),
        volume=get_volume_by_id(service.get_drive()),
    )


@strawberry.type
class Service:
    id: str
    display_name: str
    description: str
    svg_icon: str
    is_movable: bool
    is_required: bool
    is_enabled: bool
    status: ServiceStatusEnum
    url: typing.Optional[str]
    dns_records: typing.Optional[typing.List[DnsRecord]]

    @strawberry.field
    def storage_usage(self, info: Info) -> ServiceStorageUsage:
        """Get storage usage for a service"""
        locale = info.context["locale"]
        return get_storage_usage(self, locale)

    @strawberry.field
    def backup_snapshots(self) -> typing.Optional[typing.List[SnapshotInfo]]:
        return None


def service_to_graphql_service(service: ServiceInterface, locale: str) -> Service:
    """Convert service to graphql service"""
    l10n = L10n()
    return Service(
        id=service.get_id(),
        display_name=l10n.get(service.get_display_name(), locale),
        description=l10n.get(service.get_description(), locale),
        svg_icon=service.get_svg_icon(),
        is_movable=service.is_movable(),
        is_required=service.is_required(),
        is_enabled=service.is_enabled(),
        status=ServiceStatusEnum(service.get_status().value),
        url=service.get_url(),
        dns_records=[
            DnsRecord(
                record_type=record.type,
                name=record.name,
                content=record.content,
                ttl=record.ttl,
                priority=record.priority,
            )
            for record in service.get_dns_records()
        ],
    )


def get_volume_by_id(volume_id: str) -> typing.Optional[StorageVolume]:
    """Get volume by id"""
    volume = BlockDevices().get_block_device(volume_id)
    if volume is None:
        return None
    return StorageVolume(
        total_space=str(volume.fssize)
        if volume.fssize is not None
        else str(volume.size),
        free_space=str(volume.fsavail),
        used_space=str(volume.fsused),
        root=volume.name == "sda1",
        name=volume.name,
        model=volume.model,
        serial=volume.serial,
        type=volume.type,
    )
