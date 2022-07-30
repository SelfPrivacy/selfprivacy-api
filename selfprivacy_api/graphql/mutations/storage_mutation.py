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

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def mount_volume(self, name: str) -> GenericMutationReturn:
        """Mount volume"""
        volume = BlockDevices().get_block_device(name)
        if volume is None:
            return GenericMutationReturn(
                success=False, code=404, message="Volume not found"
            )
        is_success = volume.mount()
        if is_success:
            return GenericMutationReturn(
                success=True,
                code=200,
                message="Volume mounted, rebuild the system to apply changes",
            )
        return GenericMutationReturn(
            success=False, code=409, message="Volume not mounted (already mounted?)"
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def unmount_volume(self, name: str) -> GenericMutationReturn:
        """Unmount volume"""
        volume = BlockDevices().get_block_device(name)
        if volume is None:
            return GenericMutationReturn(
                success=False, code=404, message="Volume not found"
            )
        is_success = volume.unmount()
        if is_success:
            return GenericMutationReturn(
                success=True,
                code=200,
                message="Volume unmounted, rebuild the system to apply changes",
            )
        return GenericMutationReturn(
            success=False, code=409, message="Volume not unmounted (already unmounted?)"
        )
