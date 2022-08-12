"""Storage queries."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql.common_types.service import (
    ServiceStorageUsage,
    service_to_graphql_service,
    get_volume_by_id,
)
from selfprivacy_api.graphql.common_types.service import (
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
            )
            for volume in BlockDevices().get_block_devices()
        ]
