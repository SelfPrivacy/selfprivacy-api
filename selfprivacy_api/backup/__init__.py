from typing import List, Optional
from datetime import datetime, timedelta
from os import statvfs

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.utils import ReadUserData

from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import Service

from selfprivacy_api.graphql.queries.providers import BackupProvider

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.jobs import (
    get_backup_job,
    add_backup_job,
    get_restore_job,
    add_restore_job,
)
from selfprivacy_api.jobs import Jobs, JobStatus


class Backups:
    """A singleton controller for backups"""

    provider: AbstractBackupProvider

    @staticmethod
    def set_localfile_repo(file_path: str):
        ProviderClass = get_provider(BackupProvider.FILE)
        provider = ProviderClass(login="", key="", location=file_path, repo_id="")
        Storage.store_provider(provider)

    def set_provider(provider: AbstractBackupProvider):
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
    def set_provider(kind: str, login: str, key: str, location: str, repo_id: str = ""):
        provider = Backups.construct_provider(kind, login, key, location, id)
        Storage.store_provider(provider)

    @staticmethod
    def construct_provider(
        kind: str, login: str, key: str, location: str, repo_id: str = ""
    ):
        provider_class = get_provider(BackupProvider[kind])

        return provider_class(login=login, key=key, location=location, repo_id=repo_id)

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
                    location = user_data["backblaze"]["bucket"]
                    provider_string = "BACKBLAZE"
                    return Backups.construct_provider(
                        kind=provider_string, login=account, key=key, location=location
                    )
                return None

            account = user_data["backup"]["accountId"]
            key = user_data["backup"]["accountKey"]
            provider_string = user_data["backup"]["provider"]
            location = user_data["backup"]["bucket"]
            return Backups.construct_provider(
                kind=provider_string, login=account, key=key, location=location
            )

    @staticmethod
    def load_provider_redis() -> AbstractBackupProvider:
        provider_model = Storage.load_provider()
        if provider_model is None:
            return None
        return Backups.construct_provider(
            provider_model.kind,
            provider_model.login,
            provider_model.key,
            provider_model.location,
            provider_model.repo_id,
        )

    @staticmethod
    def back_up(service: Service):
        """The top-level function to back up a service"""
        folders = service.get_folders()
        repo_name = service.get_id()

        job = get_backup_job(service)
        if job is None:
            job = add_backup_job(service)
        Jobs.update(job, status=JobStatus.RUNNING)

        try:
            service.pre_backup()
            snapshot = Backups.provider().backuper.start_backup(folders, repo_name)
            Backups._store_last_snapshot(repo_name, snapshot)
            service.post_restore()
        except Exception as e:
            Jobs.update(job, status=JobStatus.ERROR)
            raise e

        Jobs.update(job, status=JobStatus.FINISHED)
        return snapshot

    @staticmethod
    def init_repo(service: Optional[Service] = None):
        if service is not None:
            repo_name = service.get_id()

        Backups.provider().backuper.init()
        Storage.mark_as_init()

    @staticmethod
    def is_initted() -> bool:
        if Storage.has_init_mark():
            return True

        initted = Backups.provider().backuper.is_initted()
        if initted:
            Storage.mark_as_init()
            return True

        return False

    @staticmethod
    def get_snapshots(service: Service) -> List[Snapshot]:
        snapshots = Backups.get_all_snapshots()
        return [snap for snap in snapshots if snap.service_name == service.get_id()]

    @staticmethod
    def get_all_snapshots() -> List[Snapshot]:
        cached_snapshots = Storage.get_cached_snapshots()
        if cached_snapshots != []:
            return cached_snapshots
        # TODO: the oldest snapshots will get expired faster than the new ones.
        # How to detect that the end is missing?

        upstream_snapshots = Backups.provider().backuper.get_snapshots()
        Backups.sync_all_snapshots()
        return upstream_snapshots

    @staticmethod
    def get_snapshot_by_id(id: str) -> Optional[Snapshot]:
        snap = Storage.get_cached_snapshot_by_id(id)
        if snap is not None:
            return snap

        # Possibly our cache entry got invalidated, let's try one more time
        Backups.sync_all_snapshots()
        snap = Storage.get_cached_snapshot_by_id(id)

        return snap

    @staticmethod
    def force_snapshot_reload():
        Backups.sync_all_snapshots()

    @staticmethod
    def sync_all_snapshots():
        upstream_snapshots = Backups.provider().backuper.get_snapshots()
        Storage.invalidate_snapshot_storage()
        for snapshot in upstream_snapshots:
            Storage.cache_snapshot(snapshot)

    # to be deprecated/internalized in favor of restore_snapshot()
    @staticmethod
    def restore_service_from_snapshot(service: Service, snapshot_id: str):
        repo_name = service.get_id()
        folders = service.get_folders()

        Backups.provider().backuper.restore_from_backup(repo_name, snapshot_id, folders)

    @staticmethod
    def assert_restorable(snapshot: Snapshot):
        service = get_service_by_id(snapshot.service_name)
        if service is None:
            raise ValueError(
                f"snapshot has a nonexistent service: {snapshot.service_name}"
            )

        needed_space = Backups.snapshot_restored_size(snapshot)
        available_space = Backups.space_usable_for_service(service)
        if needed_space > available_space:
            raise ValueError(
                f"we only have {available_space} bytes but snapshot needs{ needed_space}"
            )

    @staticmethod
    def restore_snapshot(snapshot: Snapshot):
        service = get_service_by_id(snapshot.service_name)

        job = get_restore_job(service)
        if job is None:
            job = add_restore_job(snapshot)

        Jobs.update(job, status=JobStatus.RUNNING)
        try:
            Backups.assert_restorable(snapshot)
            Backups.restore_service_from_snapshot(service, snapshot.id)
            service.post_restore()
        except Exception as e:
            Jobs.update(job, status=JobStatus.ERROR)
            raise e

        Jobs.update(job, status=JobStatus.FINISHED)

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
    def space_usable_for_service(service: Service) -> bool:
        folders = service.get_folders()
        if folders == []:
            raise ValueError("unallocated service", service.get_id())

        fs_info = statvfs(folders[0])
        usable_bytes = fs_info.f_frsize * fs_info.f_bavail
        return usable_bytes

    @staticmethod
    def _store_last_snapshot(service_id: str, snapshot: Snapshot):
        """What do we do with a snapshot that is just made?"""
        # non-expiring timestamp of the last
        Storage.store_last_timestamp(service_id, snapshot)
        # expiring cache entry
        Storage.cache_snapshot(snapshot)
