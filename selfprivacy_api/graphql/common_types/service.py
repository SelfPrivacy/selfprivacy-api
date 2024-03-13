from enum import Enum
from typing import Optional, List
import datetime
import strawberry

from selfprivacy_api.graphql.common_types.backup import BackupReason
from selfprivacy_api.graphql.common_types.dns import DnsRecord

from selfprivacy_api.services import get_service_by_id, get_services_by_location
from selfprivacy_api.services import Service as ServiceInterface
from selfprivacy_api.services import ServiceDnsRecord

from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.utils.network import get_ip4, get_ip6


def get_usages(root: "StorageVolume") -> list["StorageUsageInterface"]:
    """Get usages of a volume"""
    return [
        ServiceStorageUsage(
            service=service_to_graphql_service(service),
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


def get_storage_usage(root: "Service") -> ServiceStorageUsage:
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
        service=service_to_graphql_service(service),
        title=service.get_display_name(),
        used_space=str(service.get_storage_usage()),
        volume=get_volume_by_id(service.get_drive()),
    )


def service_dns_to_graphql(record: ServiceDnsRecord):
    # Do we really need 2 types for this?
    # ServiceDNSRecord and DnsRecord are almost identical
    return DnsRecord(
        record_type=record.type,
        name=record.name,
        content=record.content,
        ttl=record.ttl,
        priority=record.priority,
        display_name=record.display_name,
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
    can_be_backed_up: bool
    backup_description: str
    status: ServiceStatusEnum
    url: Optional[str]

    @strawberry.field
    def dns_records(self) -> Optional[List[DnsRecord]]:
        service = get_service_by_id(self.id)
        if service is None:
            raise LookupError(f"no service {self.id}. Should be unreachable")

        raw_records = service.get_dns_records(get_ip4(), get_ip6())
        dns_records = [service_dns_to_graphql(record) for record in raw_records]
        return dns_records

    @strawberry.field
    def storage_usage(self) -> ServiceStorageUsage:
        """Get storage usage for a service"""
        return get_storage_usage(self)

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
        can_be_backed_up=service.can_be_backed_up(),
        backup_description=service.get_backup_description(),
        status=ServiceStatusEnum(service.get_status().value),
        url=service.get_url(),
    )


def get_volume_by_id(volume_id: str) -> Optional[StorageVolume]:
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
