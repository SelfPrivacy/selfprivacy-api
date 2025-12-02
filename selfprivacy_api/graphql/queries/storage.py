"""Storage queries."""

# pylint: disable=too-few-public-methods
import typing
import strawberry
from opentelemetry import trace

from selfprivacy_api.graphql.common_types.service import (
    StorageVolume,
)
from selfprivacy_api.utils.block_devices import BlockDevices

tracer = trace.get_tracer(__name__)


@strawberry.type
class Storage:
    """GraphQL queries to get storage information."""

    @strawberry.field
    async def volumes(self) -> typing.List[StorageVolume]:
        """Get list of volumes"""
        with tracer.start_as_current_span("Storage.volumes"):
            return [
                StorageVolume(
                    total_space=(
                        str(volume.fssize)
                        if volume.fssize is not None
                        else str(volume.size)
                    ),
                    free_space=str(volume.fsavail),
                    used_space=str(volume.fsused),
                    root=volume.is_root(),
                    name=volume.canonical_name,
                    model=volume.model,
                    serial=volume.serial,
                    type=volume.type,
                )
                for volume in BlockDevices().get_block_devices()
            ]
