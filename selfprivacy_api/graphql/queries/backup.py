"""Backup"""
# pylint: disable=too-few-public-methods
import typing
import strawberry


from selfprivacy_api.backup import Backups
from selfprivacy_api.backup.local_secret import LocalBackupSecret
from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.graphql.common_types.service import SnapshotInfo


@strawberry.type
class BackupConfiguration:
    provider: BackupProvider
    # When server is lost, the app should have the key to decrypt backups on a new server
    encryption_key: str
    # False when repo is not initialized and not ready to be used
    is_initialized: bool
    # If none, autobackups are disabled
    autobackup_period: typing.Optional[int]
    # Bucket name for Backblaze, path for some other providers
    location_name: typing.Optional[str]
    location_id: typing.Optional[str]


@strawberry.type
class Backup:
    @strawberry.field
    def configuration(self) -> BackupConfiguration:
        encryption_key = LocalBackupSecret.get()
        return BackupConfiguration(
            provider=BackupProvider[Backups.provider().name],
            encryption_key=encryption_key.decode() if encryption_key else "",
            is_initialized=Backups.is_initted(),
            autobackup_period=Backups.autobackup_period_minutes(),
            location_name=Backups.provider().location,
            location_id=Backups.provider().repo_id,
        )

    @strawberry.field
    def all_snapshots(self) -> typing.List[SnapshotInfo]:
        result = []
        snapshots = Backups.get_all_snapshots()
        for snap in snapshots:
            graphql_snap = SnapshotInfo(
                id=snap.id, service=snap.service_name, created_at=snap.created_at
            )
            result.append(graphql_snap)
        return result
