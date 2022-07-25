"""Storage queries."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.utils.block_devices import BlockDevices


@strawberry.type
class StorageVolume:
    total_space: int
    free_space: int
    used_space: int
    root: bool
    name: str


@strawberry.type
class Storage:
    @strawberry.field
    def volumes(self) -> typing.List[StorageVolume]:
        """Get list of volumes"""
        return [
            StorageVolume(
                total_space=volume.fssize if volume.fssize is not None else volume.size,
                free_space=volume.fsavail,
                used_space=volume.fsused,
                root=volume.name == "sda1",
                name=volume.name,
            )
            for volume in BlockDevices().get_block_devices()
        ]
