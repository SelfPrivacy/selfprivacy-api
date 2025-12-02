"""Storage devices mutations"""

import strawberry
from opentelemetry import trace
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.jobs.migrate_to_binds import (
    BindMigrationConfig,
    is_bind_migrated,
    start_bind_migration,
)

tracer = trace.get_tracer(__name__)


@strawberry.input
class MigrateToBindsInput:
    """Migrate to binds input"""

    email_block_device: str
    bitwarden_block_device: str
    gitea_block_device: str
    nextcloud_block_device: str
    pleroma_block_device: str


@strawberry.type
class StorageMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def resize_volume(self, name: str) -> GenericMutationReturn:
        """Resize volume"""
        with tracer.start_as_current_span(
            "resize_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
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
        with tracer.start_as_current_span(
            "mount_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
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
        with tracer.start_as_current_span(
            "unmount_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
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
                success=False,
                code=409,
                message="Volume not unmounted (already unmounted?)",
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def migrate_to_binds(self, input: MigrateToBindsInput) -> GenericJobMutationReturn:
        """Migrate to binds"""
        with tracer.start_as_current_span("migrate_to_binds_mutation"):
            if is_bind_migrated():
                return GenericJobMutationReturn(
                    success=False, code=409, message="Already migrated to binds"
                )
            job = start_bind_migration(
                BindMigrationConfig(
                    email_block_device=input.email_block_device,
                    bitwarden_block_device=input.bitwarden_block_device,
                    gitea_block_device=input.gitea_block_device,
                    nextcloud_block_device=input.nextcloud_block_device,
                    pleroma_block_device=input.pleroma_block_device,
                )
            )
            return GenericJobMutationReturn(
                success=True,
                code=200,
                message="Migration to binds started, rebuild the system to apply changes",
                job=job_to_api_job(job),
            )
