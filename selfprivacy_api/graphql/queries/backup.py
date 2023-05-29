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
    # If none, autobackups are disabled
    autobackup_period: typing.Optional[int] = None
    # Bucket name for Backblaze, path for some other providers
    location_name: typing.Optional[str] = None
    location_id: typing.Optional[str] = None
    # False when repo is not initialized and not ready to be used
    is_initialized: bool


@strawberry.type
class Backup:
    @strawberry.field
    def configuration() -> BackupConfiguration:
        config = BackupConfiguration()
        config.encryption_key = LocalBackupSecret.get()
        config.is_initialized = Backups.is_initted()
        config.autobackup_period = Backups.autobackup_period_minutes()
        config.location_name = Backups.provider().location
        config.location_id = Backups.provider().repo_id

    @strawberry.field
    def all_snapshots(self) -> typing.List[SnapshotInfo]:
        return []
