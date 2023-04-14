from typing import List, Optional
from datetime import datetime, timedelta

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.utils.redis_pool import RedisPool


from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import Service

from selfprivacy_api.graphql.queries.providers import BackupProvider

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider
from selfprivacy_api.backup.storage import Storage


class Backups:
    """A singleton controller for backups"""

    provider: AbstractBackupProvider

    @staticmethod
    def set_localfile_repo(file_path: str):
        ProviderClass = get_provider(BackupProvider.FILE)
        provider = ProviderClass(file_path)
        Storage.store_testrepo_path(file_path)
        Storage.store_provider(provider)

    @staticmethod
    def get_last_backed_up(service: Service) -> Optional[datetime]:
        """Get a timezone-aware time of the last backup of a service"""
        return Storage.get_last_backup_time(service.get_id())

    @staticmethod
    def get_cached_snapshots_service(service_id: str) -> List[Snapshot]:
        snapshots = Storage.get_cached_snapshots()
        return [snap for snap in snapshots if snap.service_name == service_id]

    @staticmethod
    def sync_service_snapshots(service_id: str, snapshots: List[Snapshot]):
        for snapshot in snapshots:
            if snapshot.service_name == service_id:
                Storage.cache_snapshot(snapshot)
        for snapshot in Backups.get_cached_snapshots_service(service_id):
            if snapshot.id not in [snap.id for snap in snapshots]:
                Storage.delete_cached_snapshot(snapshot)

    @staticmethod
    def enable_autobackup(service: Service):
        Storage.set_autobackup(service)

    @staticmethod
    def _service_ids_to_back_up(time: datetime) -> List[str]:
        services = Storage.services_with_autobackup()
        return [id for id in services if Backups.is_time_to_backup_service(id, time)]

    @staticmethod
    def services_to_back_up(time: datetime) -> List[Service]:
        result = []
        for id in Backups._service_ids_to_back_up(time):
            service = get_service_by_id(id)
            if service is None:
                raise ValueError("Cannot look up a service scheduled for backup!")
            result.append(service)
        return result

    @staticmethod
    def is_time_to_backup(time: datetime) -> bool:
        """
        Intended as a time validator for huey cron scheduler of automatic backups
        """

        return Backups._service_ids_to_back_up(time) != []

    @staticmethod
    def is_time_to_backup_service(service_id: str, time: datetime):
        period = Backups.autobackup_period_minutes()
        if period is None:
            return False
        if not Storage.is_autobackup_set(service_id):
            return False

        last_backup = Storage.get_last_backup_time(service_id)
        if last_backup is None:
            return True  # queue a backup immediately if there are no previous backups

        if time > last_backup + timedelta(minutes=period):
            return True
        return False

    @staticmethod
    def disable_autobackup(service: Service):
        """also see disable_all_autobackup()"""
        Storage.unset_autobackup(service)

    @staticmethod
    def is_autobackup_enabled(service: Service) -> bool:
        return Storage.is_autobackup_set(service.get_id())

    @staticmethod
    def autobackup_period_minutes() -> Optional[int]:
        """None means autobackup is disabled"""
        return Storage.autobackup_period_minutes()

    @staticmethod
    def set_autobackup_period_minutes(minutes: int):
        """
        0 and negative numbers are equivalent to disable.
        Setting to a positive number may result in a backup very soon if some services are not backed up.
        """
        if minutes <= 0:
            Backups.disable_all_autobackup()
            return
        Storage.store_autobackup_period_minutes(minutes)

    @staticmethod
    def disable_all_autobackup():
        """disables all automatic backing up, but does not change per-service settings"""
        Storage.delete_backup_period()

    @staticmethod
    def provider():
        return Backups.lookup_provider()

    @staticmethod
    def set_provider(kind: str, login: str, key: str):
        provider = Backups.construct_provider(kind, login, key)
        Storage.store_provider(provider)

    @staticmethod
    def construct_provider(kind: str, login: str, key: str):
        provider_class = get_provider(BackupProvider[kind])

        if kind == "FILE":
            path = Storage.get_testrepo_path()
            return provider_class(path)

        return provider_class(login=login, key=key)

    @staticmethod
    def reset():
        Storage.reset()

    @staticmethod
    def lookup_provider() -> AbstractBackupProvider:
        redis_provider = Backups.load_provider_redis()
        if redis_provider is not None:
            return redis_provider

        json_provider = Backups.load_provider_json()
        if json_provider is not None:
            Storage.store_provider(json_provider)
            return json_provider

        memory_provider = Backups.construct_provider("MEMORY", login="", key="")
        Storage.store_provider(memory_provider)
        return memory_provider

    @staticmethod
    def load_provider_json() -> AbstractBackupProvider:
        with ReadUserData() as user_data:
            account = ""
            key = ""

            if "backup" not in user_data.keys():
                if "backblaze" in user_data.keys():
                    account = user_data["backblaze"]["accountId"]
                    key = user_data["backblaze"]["accountKey"]
                    provider_string = "BACKBLAZE"
                    return Backups.construct_provider(
                        kind=provider_string, login=account, key=key
                    )
                return None

            account = user_data["backup"]["accountId"]
            key = user_data["backup"]["accountKey"]
            provider_string = user_data["backup"]["provider"]
            return Backups.construct_provider(
                kind=provider_string, login=account, key=key
            )

    @staticmethod
    def load_provider_redis() -> AbstractBackupProvider:
        provider_model = Storage.load_provider()
        if provider_model is None:
            return None
        return Backups.construct_provider(
            provider_model.kind, provider_model.login, provider_model.key
        )

    @staticmethod
    def back_up(service: Service):
        """The top-level function to back up a service"""
        folder = service.get_folders()
        repo_name = service.get_id()

        service.pre_backup()
        snapshot = Backups.provider().backuper.start_backup(folder, repo_name)
        Backups._store_last_snapshot(repo_name, snapshot)

        service.post_restore()

    @staticmethod
    def init_repo(service: Service):
        repo_name = service.get_id()
        Backups.provider().backuper.init(repo_name)
        Storage.mark_as_init(service)

    @staticmethod
    def is_initted(service: Service) -> bool:
        repo_name = service.get_id()
        if Storage.has_init_mark(service):
            return True

        initted = Backups.provider().backuper.is_initted(repo_name)
        if initted:
            Storage.mark_as_init(service)
            return True

        return False

    @staticmethod
    def get_snapshots(service: Service) -> List[Snapshot]:
        service_id = service.get_id()
        cached_snapshots = Backups.get_cached_snapshots_service(service_id)
        if cached_snapshots != []:
            return cached_snapshots
        # TODO: the oldest snapshots will get expired faster than the new ones.
        # How to detect that the end is missing?

        upstream_snapshots = Backups.provider().backuper.get_snapshots(service_id)
        Backups.sync_service_snapshots(service_id, upstream_snapshots)
        return upstream_snapshots

    @staticmethod
    def restore_service_from_snapshot(service: Service, snapshot_id: str):
        repo_name = service.get_id()
        folder = service.get_folders()

        Backups.provider().backuper.restore_from_backup(repo_name, snapshot_id, folder)

    @staticmethod
    def restore_snapshot(snapshot: Snapshot):
        Backups.restore_service_from_snapshot(
            get_service_by_id(snapshot.service_name), snapshot.id
        )

    @staticmethod
    def service_snapshot_size(service: Service, snapshot_id: str) -> float:
        repo_name = service.get_id()
        return Backups.provider().backuper.restored_size(repo_name, snapshot_id)

    @staticmethod
    def snapshot_restored_size(snapshot: Snapshot) -> float:
        return Backups.service_snapshot_size(
            get_service_by_id(snapshot.service_name), snapshot.id
        )

    @staticmethod
    def _store_last_snapshot(service_id: str, snapshot: Snapshot):
        """What do we do with a snapshot that is just made?"""
        # non-expiring timestamp of the last
        Storage.store_last_timestamp(service_id, snapshot)
        # expiring cache entry
        Storage.cache_snapshot(snapshot)
