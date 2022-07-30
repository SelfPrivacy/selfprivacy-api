"""Storage queries."""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.utils.block_devices import BlockDevices


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
