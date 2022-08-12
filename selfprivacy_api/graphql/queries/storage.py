"""Storage queries."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql.common_types.service import (
    service_to_graphql_service,
    get_volume_by_id,
)
from selfprivacy_api.graphql.common_types.storage_usage import (
    ServiceStorageUsage,
    StorageVolume,
)
from selfprivacy_api.services import get_services_by_location
from selfprivacy_api.utils.block_devices import BlockDevices


@strawberry.type
class Storage:
    """GraphQL queries to get storage information."""

    @strawberry.field
    def volumes(self) -> typing.List[StorageVolume]:
        """Get list of volumes"""
        return [
            StorageVolume(
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
                usages=[
                    ServiceStorageUsage(
                        service=service_to_graphql_service(service),
                        title=service.get_display_name(),
                        used_space=str(service.get_storage_usage()),
                        volume=get_volume_by_id(service.get_location()),
                    )
                    for service in get_services_by_location(volume.name)
                ],
            )
            for volume in BlockDevices().get_block_devices()
        ]
