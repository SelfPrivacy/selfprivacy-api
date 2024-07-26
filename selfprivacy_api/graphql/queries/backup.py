"""Backup"""

# pylint: disable=too-few-public-methods
import typing
import strawberry


from selfprivacy_api.backup import Backups
from selfprivacy_api.backup.local_secret import LocalBackupSecret
from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.graphql.common_types.service import (
    Service,
    ServiceStatusEnum,
    SnapshotInfo,
    service_to_graphql_service,
)
from selfprivacy_api.graphql.common_types.backup import AutobackupQuotas
from selfprivacy_api.services import get_service_by_id


@strawberry.type
class BackupConfiguration:
    provider: BackupProvider
    # When server is lost, the app should have the key to decrypt backups
    # on a new server
    encryption_key: str
    # False when repo is not initialized and not ready to be used
    is_initialized: bool
    # If none, autobackups are disabled
    autobackup_period: typing.Optional[int]
    # None is equal to all quotas being unlimited (-1). Optional for compatibility reasons.
    autobackup_quotas: AutobackupQuotas
    # Bucket name for Backblaze, path for some other providers
    location_name: typing.Optional[str]
    location_id: typing.Optional[str]


# TODO: Ideally this should not be done in API but making an internal Service requires more work
# than to make an API record about a service
def tombstone_service(service_id: str) -> Service:
    return Service(
        id=service_id,
        display_name=f"{service_id} (Orphaned)",
        description="",
        svg_icon="",
        is_movable=False,
        is_required=False,
        is_enabled=False,
        status=ServiceStatusEnum.OFF,
        url=None,
        can_be_backed_up=False,
        backup_description="",
        is_installed=False,
    )


@strawberry.type
class Backup:
    @strawberry.field
    def configuration(self) -> BackupConfiguration:
        return BackupConfiguration(
            provider=Backups.provider().name,
            encryption_key=LocalBackupSecret.get(),
            is_initialized=Backups.is_initted(),
            autobackup_period=Backups.autobackup_period_minutes(),
            location_name=Backups.provider().location,
            location_id=Backups.provider().repo_id,
            autobackup_quotas=Backups.autobackup_quotas(),
        )

    @strawberry.field
    def all_snapshots(self) -> typing.List[SnapshotInfo]:
        if not Backups.is_initted():
            return []
        result = []
        snapshots = Backups.get_all_snapshots()
        for snap in snapshots:
            api_service = None
            service = get_service_by_id(snap.service_name)

            if service is None:
                api_service = tombstone_service(snap.service_name)
            else:
                api_service = service_to_graphql_service(service)
            if api_service is None:
                raise NotImplementedError(
                    f"Could not construct API Service record for:{snap.service_name}. This should be unreachable and is a bug if you see it."
                )

            graphql_snap = SnapshotInfo(
                id=snap.id,
                service=api_service,
                created_at=snap.created_at,
                reason=snap.reason,
            )
            result.append(graphql_snap)
        return result
