"""Storage devices mutations"""

import gettext

import strawberry
from opentelemetry import trace
from strawberry.types import Info

from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.utils.localization import (
    TranslateSystemMessage as t,
    DEFAULT_LOCALE,
)
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.jobs import job_to_api_job
from selfprivacy_api.graphql.mutations.mutation_interface import (
    GenericJobMutationReturn,
    GenericMutationReturn,
)
from selfprivacy_api.graphql.queries.jobs import translate_job

from selfprivacy_api.jobs.migrate_to_binds import (
    BindMigrationConfig,
    is_bind_migrated,
    start_bind_migration,
)

tracer = trace.get_tracer(__name__)
_ = gettext.gettext

VOLUME_NOT_FOUND = _("Volume not found")


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
    def resize_volume(self, name: str, info: Info) -> GenericMutationReturn:
        """Resize volume"""
        locale = (
            info.context.get("locale") if info.context.get("locale") else DEFAULT_LOCALE
        )

        with tracer.start_as_current_span(
            "resize_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
            if volume is None:
                return GenericMutationReturn(
                    success=False,
                    code=404,
                    message=t.translate(text=VOLUME_NOT_FOUND, locale=locale),
                )
            volume.resize()
            return GenericMutationReturn(
                success=True,
                code=200,
                message=t.translate(text=_("Volume resize started"), locale=locale),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def mount_volume(self, name: str, info: Info) -> GenericMutationReturn:
        """Mount volume"""
        locale = (
            info.context.get("locale") if info.context.get("locale") else DEFAULT_LOCALE
        )

        with tracer.start_as_current_span(
            "mount_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
            if volume is None:
                return GenericMutationReturn(
                    success=False,
                    code=404,
                    message=t.translate(text=VOLUME_NOT_FOUND, locale=locale),
                )
            is_success = volume.mount()
            if is_success:
                return GenericMutationReturn(
                    success=True,
                    code=200,
                    message=t.translate(
                        text=_("Volume mounted, rebuild the system to apply changes"),
                        locale=locale,
                    ),
                )
            return GenericMutationReturn(
                success=False,
                code=409,
                message=t.translate(
                    text=_("Volume not mounted (already mounted?)"), locale=locale
                ),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def unmount_volume(self, name: str, info: Info) -> GenericMutationReturn:
        """Unmount volume"""
        locale = (
            info.context.get("locale") if info.context.get("locale") else DEFAULT_LOCALE
        )

        with tracer.start_as_current_span(
            "unmount_volume_mutation",
            attributes={
                "name": name,
            },
        ):
            volume = BlockDevices().get_block_device_by_canonical_name(name)
            if volume is None:
                return GenericMutationReturn(
                    success=False,
                    code=404,
                    message=t.translate(text=VOLUME_NOT_FOUND, locale=locale),
                )
            is_success = volume.unmount()
            if is_success:
                return GenericMutationReturn(
                    success=True,
                    code=200,
                    message=t.translate(
                        text=_("Volume unmounted, rebuild the system to apply changes"),
                        locale=locale,
                    ),
                )
            return GenericMutationReturn(
                success=False,
                code=409,
                message=t.translate(
                    text=_("Volume not unmounted (already unmounted?)"), locale=locale
                ),
            )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def migrate_to_binds(
        self, input: MigrateToBindsInput, info: Info
    ) -> GenericJobMutationReturn:
        """Migrate to binds"""
        locale = (
            info.context.get("locale") if info.context.get("locale") else DEFAULT_LOCALE
        )

        with tracer.start_as_current_span("migrate_to_binds_mutation"):
            if is_bind_migrated():
                return GenericJobMutationReturn(
                    success=False,
                    code=409,
                    message=t.translate(
                        text=_("Already migrated to binds"), locale=locale
                    ),
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
                message=t.translate(
                    text=_(
                        "Migration to binds started, rebuild the system to apply changes"
                    ),
                    locale=locale,
                ),
                job=translate_job(job=job_to_api_job(job), locale=locale),
            )
