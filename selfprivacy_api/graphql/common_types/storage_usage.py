import typing
import strawberry


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
    usages: list["StorageUsageInterface"]


@strawberry.interface
class StorageUsageInterface:
    used_space: str
    volume: typing.Optional[StorageVolume]
    title: str
