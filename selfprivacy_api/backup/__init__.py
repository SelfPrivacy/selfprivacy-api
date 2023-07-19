from datetime import datetime, timedelta
from os import statvfs
from typing import List, Optional

from selfprivacy_api.utils import ReadUserData, WriteUserData

from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import (
    Service,
    ServiceStatus,
    StoppedService,
)

from selfprivacy_api.jobs import Jobs, JobStatus, Job

from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)
from selfprivacy_api.graphql.common_types.backup import RestoreStrategy

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.jobs import (
    get_backup_job,
    add_backup_job,
    get_restore_job,
    add_restore_job,
)

DEFAULT_JSON_PROVIDER = {
    "provider": "BACKBLAZE",
    "accountId": "",
    "accountKey": "",
    "bucket": "",
}


class NotDeadError(AssertionError):
    def __init__(self, service: Service):
        self.service_name = service.get_id()

    def __str__(self):
        return f"""
        Service {self.service_name} should be either stopped or dead from
        an error before we back up.
        Normally, this error is unreachable because we do try ensure this.
        Apparently, not this time.
        """


class Backups:
    """A stateless controller class for backups"""

    # Providers

    @staticmethod
    def provider() -> AbstractBackupProvider:
        return Backups._lookup_provider()

    @staticmethod
    def set_provider(
        kind: BackupProviderEnum,
        login: str,
        key: str,
        location: str,
        repo_id: str = "",
    ) -> None:
        provider: AbstractBackupProvider = Backups._construct_provider(
            kind,
            login,
            key,
            location,
            repo_id,
        )
        Storage.store_provider(provider)

    @staticmethod
    def reset(reset_json=True) -> None:
        Storage.reset()
        if reset_json:
            try:
                Backups._reset_provider_json()
            except FileNotFoundError:
                # if there is no userdata file, we do not need to reset it
                pass

    @staticmethod
    def _lookup_provider() -> AbstractBackupProvider:
        redis_provider = Backups._load_provider_redis()
        if redis_provider is not None:
            return redis_provider

        try:
            json_provider = Backups._load_provider_json()
        except FileNotFoundError:
            json_provider = None

        if json_provider is not None:
            Storage.store_provider(json_provider)
            return json_provider

        none_provider = Backups._construct_provider(
            BackupProviderEnum.NONE, login="", key="", location=""
        )
        Storage.store_provider(none_provider)
        return none_provider

    @staticmethod
    def _construct_provider(
        kind: BackupProviderEnum,
        login: str,
        key: str,
        location: str,
        repo_id: str = "",
    ) -> AbstractBackupProvider:
        provider_class = get_provider(kind)

        return provider_class(
            login=login,
            key=key,
            location=location,
            repo_id=repo_id,
        )

    @staticmethod
    def _load_provider_redis() -> Optional[AbstractBackupProvider]:
        provider_model = Storage.load_provider()
        if provider_model is None:
            return None
        return Backups._construct_provider(
            BackupProviderEnum[provider_model.kind],
            provider_model.login,
            provider_model.key,
            provider_model.location,
            provider_model.repo_id,
        )

    @staticmethod
    def _load_provider_json() -> Optional[AbstractBackupProvider]:
        with ReadUserData() as user_data:
            provider_dict = {
                "provider": "",
                "accountId": "",
                "accountKey": "",
                "bucket": "",
            }

            if "backup" not in user_data.keys():
                if "backblaze" in user_data.keys():
                    provider_dict.update(user_data["backblaze"])
                    provider_dict["provider"] = "BACKBLAZE"
                return None
            else:
                provider_dict.update(user_data["backup"])

            if provider_dict == DEFAULT_JSON_PROVIDER:
                return None
            try:
                return Backups._construct_provider(
                    kind=BackupProviderEnum[provider_dict["provider"]],
                    login=provider_dict["accountId"],
                    key=provider_dict["accountKey"],
                    location=provider_dict["bucket"],
                )
            except KeyError:
                return None

    @staticmethod
    def _reset_provider_json() -> None:
        with WriteUserData() as user_data:
            if "backblaze" in user_data.keys():
                del user_data["backblaze"]

            user_data["backup"] = DEFAULT_JSON_PROVIDER

    # Init

    @staticmethod
    def init_repo() -> None:
        Backups.provider().backupper.init()
        Storage.mark_as_init()

    @staticmethod
    def is_initted() -> bool:
        if Storage.has_init_mark():
            return True

        initted = Backups.provider().backupper.is_initted()
        if initted:
            Storage.mark_as_init()
            return True

        return False

    # Backup

    @staticmethod
    def back_up(service: Service) -> Snapshot:
        """The top-level function to back up a service"""
        folders = service.get_folders()
        tag = service.get_id()

        job = get_backup_job(service)
        if job is None:
            job = add_backup_job(service)
        Jobs.update(job, status=JobStatus.RUNNING)

        try:
            with StoppedService(service):
                Backups.assert_dead(service)  # to be extra sure
                service.pre_backup()
                snapshot = Backups.provider().backupper.start_backup(
                    folders,
                    tag,
                )
                Backups._store_last_snapshot(tag, snapshot)
                service.post_restore()
        except Exception as e:
            Jobs.update(job, status=JobStatus.ERROR)
            raise e

        Jobs.update(job, status=JobStatus.FINISHED)
        return snapshot

    # Restoring

    @staticmethod
    def _ensure_queued_restore_job(service, snapshot) -> Job:
        job = get_restore_job(service)
        if job is None:
            job = add_restore_job(snapshot)

        Jobs.update(job, status=JobStatus.CREATED)
        return job

    @staticmethod
    def _inplace_restore(
        service: Service,
        snapshot: Snapshot,
        job: Job,
    ) -> None:
        failsafe_snapshot = Backups.back_up(service)

        Jobs.update(job, status=JobStatus.RUNNING)
        try:
            Backups._restore_service_from_snapshot(
                service,
                snapshot.id,
                verify=False,
            )
        except Exception as e:
            Backups._restore_service_from_snapshot(
                service, failsafe_snapshot.id, verify=False
            )
            raise e

    @staticmethod
    def restore_snapshot(
        snapshot: Snapshot, strategy=RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE
    ) -> None:
        service = get_service_by_id(snapshot.service_name)
        if service is None:
            raise ValueError(
                f"snapshot has a nonexistent service: {snapshot.service_name}"
            )
        job = Backups._ensure_queued_restore_job(service, snapshot)

        try:
            Backups._assert_restorable(snapshot)
            with StoppedService(service):
                Backups.assert_dead(service)
                if strategy == RestoreStrategy.INPLACE:
                    Backups._inplace_restore(service, snapshot, job)
                else:  # verify_before_download is our default
                    Jobs.update(job, status=JobStatus.RUNNING)
                    Backups._restore_service_from_snapshot(
                        service, snapshot.id, verify=True
                    )

                service.post_restore()

        except Exception as e:
            Jobs.update(job, status=JobStatus.ERROR)
            raise e

        Jobs.update(job, status=JobStatus.FINISHED)

    @staticmethod
    def _assert_restorable(
        snapshot: Snapshot, strategy=RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE
    ) -> None:
        service = get_service_by_id(snapshot.service_name)
        if service is None:
            raise ValueError(
                f"snapshot has a nonexistent service: {snapshot.service_name}"
            )

        restored_snap_size = Backups.snapshot_restored_size(snapshot.id)

        if strategy == RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE:
            needed_space = restored_snap_size
        elif strategy == RestoreStrategy.INPLACE:
            needed_space = restored_snap_size - service.get_storage_usage()
        else:
            raise NotImplementedError(
                """
            We do not know if there is enough space for restoration because
            there is some novel restore strategy used!
            This is a developer's fault, open an issue please
            """
            )
        available_space = Backups.space_usable_for_service(service)
        if needed_space > available_space:
            raise ValueError(
                f"we only have {available_space} bytes "
                f"but snapshot needs {needed_space}"
            )

    @staticmethod
    def _restore_service_from_snapshot(
        service: Service,
        snapshot_id: str,
        verify=True,
    ) -> None:
        folders = service.get_folders()

        Backups.provider().backupper.restore_from_backup(
            snapshot_id,
            folders,
            verify=verify,
        )

    # Snapshots

    @staticmethod
    def get_snapshots(service: Service) -> List[Snapshot]:
        snapshots = Backups.get_all_snapshots()
        service_id = service.get_id()
        return list(
            filter(
                lambda snap: snap.service_name == service_id,
                snapshots,
            )
        )

    @staticmethod
    def get_all_snapshots() -> List[Snapshot]:
        cached_snapshots = Storage.get_cached_snapshots()
        if cached_snapshots != []:
            return cached_snapshots
        # TODO: the oldest snapshots will get expired faster than the new ones.
        # How to detect that the end is missing?

        Backups.force_snapshot_cache_reload()
        return Storage.get_cached_snapshots()

    @staticmethod
    def get_snapshot_by_id(id: str) -> Optional[Snapshot]:
        snap = Storage.get_cached_snapshot_by_id(id)
        if snap is not None:
            return snap

        # Possibly our cache entry got invalidated, let's try one more time
        Backups.force_snapshot_cache_reload()
        snap = Storage.get_cached_snapshot_by_id(id)

        return snap

    @staticmethod
    def forget_snapshot(snapshot: Snapshot) -> None:
        Backups.provider().backupper.forget_snapshot(snapshot.id)
        Storage.delete_cached_snapshot(snapshot)

    @staticmethod
    def force_snapshot_cache_reload() -> None:
        upstream_snapshots = Backups.provider().backupper.get_snapshots()
        Storage.invalidate_snapshot_storage()
        for snapshot in upstream_snapshots:
            Storage.cache_snapshot(snapshot)

    @staticmethod
    def snapshot_restored_size(snapshot_id: str) -> int:
        return Backups.provider().backupper.restored_size(
            snapshot_id,
        )

    @staticmethod
    def _store_last_snapshot(service_id: str, snapshot: Snapshot) -> None:
        """What do we do with a snapshot that is just made?"""
        # non-expiring timestamp of the last
        Storage.store_last_timestamp(service_id, snapshot)
        # expiring cache entry
        Storage.cache_snapshot(snapshot)

    # Autobackup

    @staticmethod
    def is_autobackup_enabled(service: Service) -> bool:
        return Storage.is_autobackup_set(service.get_id())

    @staticmethod
    def enable_autobackup(service: Service) -> None:
        Storage.set_autobackup(service)

    @staticmethod
    def disable_autobackup(service: Service) -> None:
        """also see disable_all_autobackup()"""
        Storage.unset_autobackup(service)

    @staticmethod
    def disable_all_autobackup() -> None:
        """
        Disables all automatic backing up,
        but does not change per-service settings
        """
        Storage.delete_backup_period()

    @staticmethod
    def autobackup_period_minutes() -> Optional[int]:
        """None means autobackup is disabled"""
        return Storage.autobackup_period_minutes()

    @staticmethod
    def set_autobackup_period_minutes(minutes: int) -> None:
        """
        0 and negative numbers are equivalent to disable.
        Setting to a positive number may result in a backup very soon
        if some services are not backed up.
        """
        if minutes <= 0:
            Backups.disable_all_autobackup()
            return
        Storage.store_autobackup_period_minutes(minutes)

    @staticmethod
    def is_time_to_backup(time: datetime) -> bool:
        """
        Intended as a time validator for huey cron scheduler
        of automatic backups
        """

        return Backups._service_ids_to_back_up(time) != []

    @staticmethod
    def services_to_back_up(time: datetime) -> List[Service]:
        result: list[Service] = []
        for id in Backups._service_ids_to_back_up(time):
            service = get_service_by_id(id)
            if service is None:
                raise ValueError(
                    "Cannot look up a service scheduled for backup!",
                )
            result.append(service)
        return result

    @staticmethod
    def get_last_backed_up(service: Service) -> Optional[datetime]:
        """Get a timezone-aware time of the last backup of a service"""
        return Storage.get_last_backup_time(service.get_id())

    @staticmethod
    def is_time_to_backup_service(service_id: str, time: datetime):
        period = Backups.autobackup_period_minutes()
        if period is None:
            return False
        if not Storage.is_autobackup_set(service_id):
            return False

        last_backup = Storage.get_last_backup_time(service_id)
        if last_backup is None:
            # queue a backup immediately if there are no previous backups
            return True

        if time > last_backup + timedelta(minutes=period):
            return True
        return False

    @staticmethod
    def _service_ids_to_back_up(time: datetime) -> List[str]:
        services = Storage.services_with_autobackup()
        return [
            id
            for id in services
            if Backups.is_time_to_backup_service(
                id,
                time,
            )
        ]

    # Helpers

    @staticmethod
    def space_usable_for_service(service: Service) -> int:
        folders = service.get_folders()
        if folders == []:
            raise ValueError("unallocated service", service.get_id())

        # We assume all folders of one service live at the same volume
        fs_info = statvfs(folders[0])
        usable_bytes = fs_info.f_frsize * fs_info.f_bavail
        return usable_bytes

    @staticmethod
    def set_localfile_repo(file_path: str):
        ProviderClass = get_provider(BackupProviderEnum.FILE)
        provider = ProviderClass(
            login="",
            key="",
            location=file_path,
            repo_id="",
        )
        Storage.store_provider(provider)

    @staticmethod
    def assert_dead(service: Service):
        # if we backup the service that is failing to restore it to the
        # previous snapshot, its status can be FAILED
        # And obviously restoring a failed service is the main route
        if service.get_status() not in [
            ServiceStatus.INACTIVE,
            ServiceStatus.FAILED,
        ]:
            raise NotDeadError(service)
