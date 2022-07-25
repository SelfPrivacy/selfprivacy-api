"""Storage devices mutations"""
import typing
import strawberry
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericMutationReturn,
)


@strawberry.type
class StorageMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def resize_volume(self, name: str) -> GenericMutationReturn:
        """Resize volume"""
        volume = BlockDevices().get_block_device(name)
        if volume is None:
            return GenericMutationReturn(
                success=False, code=404, message="Volume not found"
            )
        volume.resize()
        return GenericMutationReturn(
            success=True, code=200, message="Volume resize started"
        )
