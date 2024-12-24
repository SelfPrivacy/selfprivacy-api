"""
This module contains the controller class for backups.
"""

from datetime import datetime, timedelta, timezone
import time
import os
from os import statvfs
from typing import Callable, List, Optional
from os.path import exists

from selfprivacy_api.services import ServiceManager

from selfprivacy_api.services.service import (
    Service,
    ServiceStatus,
    StoppedService,
)

from selfprivacy_api.jobs import Jobs, JobStatus, Job

from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)
from selfprivacy_api.graphql.common_types.backup import (
    RestoreStrategy,
    BackupReason,
    AutobackupQuotas,
)


from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.utils.block_devices import BlockDevices

from selfprivacy_api.backup.providers.provider import AbstractBackupProvider
from selfprivacy_api.backup.providers import get_provider
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.jobs import (
    get_backup_job,
    get_backup_fail,
    add_backup_job,
    get_restore_job,
    add_restore_job,
)


BACKUP_PROVIDER_ENVS = {
    "kind": "BACKUP_KIND",
    "login": "BACKUP_LOGIN",
    "key": "BACKUP_KEY",
    "location": "BACKUP_LOCATION",
}

AUTOBACKUP_JOB_EXPIRATION_SECONDS = 60 * 60  # one hour


class NotDeadError(AssertionError):
    """
    This error is raised when we try to back up a service that is not dead yet.
    """

    def __init__(self, service: Service):
        self.service_name = service.get_id()
        super().__init__()

    def __str__(self):
        return f"""
        Service {self.service_name} should be either stopped or dead from
        an error before we back up.
        Normally, this error is unreachable because we do try ensure this.
        Apparently, not this time.
        """


class RotationBucket:
    """
    Bucket object used for rotation.
    Has the following mutable fields:
    - the counter, int
    - the lambda function which takes datetime and the int and returns the int
    - the last, int
    """

    def __init__(self, counter: int, last: int, rotation_lambda):
        self.counter: int = counter
        self.last: int = last
        self.rotation_lambda: Callable[[datetime, int], int] = rotation_lambda

    def __str__(self) -> str:
        return f"Bucket(counter={self.counter}, last={self.last})"


class Backups:
    """A stateless controller class for backups"""

    # Providers

    @staticmethod
    def provider() -> AbstractBackupProvider:
        """
        Returns the current backup storage provider.
        """
        return Backups._lookup_provider()

    @staticmethod
    def set_provider(
        kind: BackupProviderEnum,
        login: str,
        key: str,
        location: str,
        repo_id: str = "",
    ) -> None:
        """
        Sets the new configuration of the backup storage provider.

        In case of `BackupProviderEnum.BACKBLAZE`, the `login` is the key ID,
        the `key` is the key itself, and the `location` is the bucket name and
        the `repo_id` is the bucket ID.
        """
        provider: AbstractBackupProvider = Backups._construct_provider(
            kind,
            login,
            key,
            location,
            repo_id,
        )
        Storage.store_provider(provider)

    @staticmethod
    def reset() -> None:
        """
        Deletes all the data about the backup storage provider.
        """
        Storage.reset()

    @staticmethod
    def _lookup_provider() -> AbstractBackupProvider:
        redis_provider = Backups._load_provider_redis()
        if redis_provider is not None:
            return redis_provider

        none_provider = Backups._construct_provider(
            BackupProviderEnum.NONE, login="", key="", location=""
        )
        Storage.store_provider(none_provider)
        return none_provider

    @staticmethod
    def set_provider_from_envs():
        for env in BACKUP_PROVIDER_ENVS.values():
            if env not in os.environ.keys():
                raise ValueError(
                    f"Cannot set backup provider from envs, there is no {env} set"
                )

        kind_str = os.environ[BACKUP_PROVIDER_ENVS["kind"]]
        kind_enum = BackupProviderEnum[kind_str]
        provider = Backups._construct_provider(
            kind=kind_enum,
            login=os.environ[BACKUP_PROVIDER_ENVS["login"]],
            key=os.environ[BACKUP_PROVIDER_ENVS["key"]],
            location=os.environ[BACKUP_PROVIDER_ENVS["location"]],
        )
        Storage.store_provider(provider)

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

    # Init

    @staticmethod
    def init_repo() -> None:
        """
        Initializes the backup repository. This is required once per repo.
        """
        Backups.provider().backupper.init()
        Storage.mark_as_init()

    @staticmethod
    def erase_repo() -> None:
        """
        Completely empties the remote
        """
        Backups.provider().backupper.erase_repo()
        Storage.mark_as_uninitted()

    @staticmethod
    def is_initted() -> bool:
        """
        Returns whether the backup repository is initialized or not.
        If it is not initialized, we cannot back up and probably should
        call `init_repo` first.
        """
        if Storage.has_init_mark():
            return True

        initted = Backups.provider().backupper.is_initted()
        if initted:
            Storage.mark_as_init()
            return True

        return False

    # Backup

    @staticmethod
    def back_up(
        service: Service, reason: BackupReason = BackupReason.EXPLICIT
    ) -> Snapshot:
        """The top-level function to back up a service
        If it fails for any reason at all, it should both mark job as
        errored and re-raise an error"""

        job = get_backup_job(service)
        if job is None:
            job = add_backup_job(service)
        Jobs.update(job, status=JobStatus.RUNNING)

        try:
            if service.can_be_backed_up() is False:
                raise ValueError("cannot backup a non-backuppable service")
            folders = service.get_folders_to_back_up()
            service_name = service.get_id()
            service.pre_backup(job=job)
            Jobs.update(job, status=JobStatus.RUNNING, status_text="Uploading backup")
            snapshot = Backups.provider().backupper.start_backup(
                folders,
                service_name,
                reason=reason,
            )

            Backups._on_new_snapshot_created(service_name, snapshot)
            if reason == BackupReason.AUTO:
                Backups._prune_auto_snaps(service)
            service.post_backup(job=job)
        except Exception as error:
            Jobs.update(job, status=JobStatus.ERROR, error=str(error))
            raise error

        Jobs.update(job, status=JobStatus.FINISHED, result="Backup finished")
        if reason in [BackupReason.AUTO, BackupReason.PRE_RESTORE]:
            Jobs.set_expiration(job, AUTOBACKUP_JOB_EXPIRATION_SECONDS)
        return Backups.sync_date_from_cache(snapshot)

    @staticmethod
    def sync_date_from_cache(snapshot: Snapshot) -> Snapshot:
        """
        Our snapshot creation dates are different from those on server by a tiny amount.
        This is a convenience, maybe it is better to write a special comparison
        function for snapshots
        """

        snap = Storage.get_cached_snapshot_by_id(snapshot.id)
        if snap is None:
            raise ValueError(
                f"snapshot {snapshot.id} date syncing failed, this should never happen normally"
            )
        return snap

    @staticmethod
    def _auto_snaps(service) -> List[Snapshot]:
        return [
            snap
            for snap in Backups.get_snapshots(service)
            if snap.reason == BackupReason.AUTO
        ]

    @staticmethod
    def _prune_snaps_with_quotas(snapshots: List[Snapshot]) -> List[Snapshot]:
        # Function broken out for testability
        # Sorting newest first
        sorted_snaps = sorted(snapshots, key=lambda s: s.created_at, reverse=True)
        quotas: AutobackupQuotas = Backups.autobackup_quotas()

        buckets: list[RotationBucket] = [
            RotationBucket(
                quotas.last,  # type: ignore
                -1,
                lambda _, index: index,
            ),
            RotationBucket(
                quotas.daily,  # type: ignore
                -1,
                lambda date, _: date.year * 10000 + date.month * 100 + date.day,
            ),
            RotationBucket(
                quotas.weekly,  # type: ignore
                -1,
                lambda date, _: date.year * 100 + date.isocalendar()[1],
            ),
            RotationBucket(
                quotas.monthly,  # type: ignore
                -1,
                lambda date, _: date.year * 100 + date.month,
            ),
            RotationBucket(
                quotas.yearly,  # type: ignore
                -1,
                lambda date, _: date.year,
            ),
        ]

        new_snaplist: List[Snapshot] = []
        for i, snap in enumerate(sorted_snaps):
            keep_snap = False
            for bucket in buckets:
                if (bucket.counter > 0) or (bucket.counter == -1):
                    val = bucket.rotation_lambda(snap.created_at, i)
                    if (val != bucket.last) or (i == len(sorted_snaps) - 1):
                        bucket.last = val
                        if bucket.counter > 0:
                            bucket.counter -= 1
                        if not keep_snap:
                            new_snaplist.append(snap)
                        keep_snap = True

        return new_snaplist

    @staticmethod
    def _prune_auto_snaps(service) -> None:
        # Not very testable by itself, so most testing is going on Backups._prune_snaps_with_quotas
        # We can still test total limits and, say, daily limits

        auto_snaps = Backups._auto_snaps(service)
        new_snaplist = Backups._prune_snaps_with_quotas(auto_snaps)

        deletable_snaps = [snap for snap in auto_snaps if snap not in new_snaplist]
        Backups.forget_snapshots(deletable_snaps)

    @staticmethod
    def _standardize_quotas(i: int) -> int:
        if i <= -1:
            i = -1
        return i

    @staticmethod
    def autobackup_quotas() -> AutobackupQuotas:
        """0 means do not keep, -1 means unlimited"""

        return Storage.autobackup_quotas()

    @staticmethod
    def set_autobackup_quotas(quotas: AutobackupQuotas) -> None:
        """0 means do not keep, -1 means unlimited"""

        Storage.set_autobackup_quotas(
            AutobackupQuotas(
                last=Backups._standardize_quotas(quotas.last),  # type: ignore
                daily=Backups._standardize_quotas(quotas.daily),  # type: ignore
                weekly=Backups._standardize_quotas(quotas.weekly),  # type: ignore
                monthly=Backups._standardize_quotas(quotas.monthly),  # type: ignore
                yearly=Backups._standardize_quotas(quotas.yearly),  # type: ignore
            )
        )
        # do not prune all autosnaps right away, this will be done by an async task

    @staticmethod
    def prune_all_autosnaps() -> None:
        for service in ServiceManager.get_all_services():
            Backups._prune_auto_snaps(service)

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
        Jobs.update(
            job, status=JobStatus.CREATED, status_text="Waiting for pre-restore backup"
        )
        failsafe_snapshot = Backups.back_up(service, BackupReason.PRE_RESTORE)

        Jobs.update(
            job, status=JobStatus.RUNNING, status_text=f"Restoring from {snapshot.id}"
        )
        try:
            Backups._restore_service_from_snapshot(
                service,
                snapshot.id,
                verify=False,
            )
        except Exception as error:
            Jobs.update(
                job,
                status=JobStatus.ERROR,
                status_text=f"Restore failed with {str(error)}, reverting to {failsafe_snapshot.id}",
            )
            Backups._restore_service_from_snapshot(
                service, failsafe_snapshot.id, verify=False
            )
            Jobs.update(
                job,
                status=JobStatus.ERROR,
                status_text=f"Restore failed with {str(error)}, reverted to {failsafe_snapshot.id}",
            )
            raise error

    @staticmethod
    def restore_snapshot(
        snapshot: Snapshot, strategy=RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE
    ) -> None:
        """Restores a snapshot to its original service using the given strategy"""
        service = ServiceManager.get_service_by_id(snapshot.service_name)
        if service is None:
            raise ValueError(
                f"snapshot has a nonexistent service: {snapshot.service_name}"
            )
        job = Backups._ensure_queued_restore_job(service, snapshot)

        try:
            Backups._assert_restorable(snapshot)
            Jobs.update(
                job, status=JobStatus.RUNNING, status_text="Stopping the service"
            )
            with StoppedService(service):
                if not service.is_always_active():
                    Backups.assert_dead(service)
                service.pre_restore(job=job)
                if strategy == RestoreStrategy.INPLACE:
                    Backups._inplace_restore(service, snapshot, job)
                else:  # verify_before_download is our default
                    Jobs.update(
                        job,
                        status=JobStatus.RUNNING,
                        status_text=f"Restoring from {snapshot.id}",
                    )
                    Backups._restore_service_from_snapshot(
                        service, snapshot.id, verify=True
                    )

                service.post_restore(job=job)
                Jobs.update(
                    job,
                    status=JobStatus.RUNNING,
                    progress=90,
                    status_text="Restarting the service",
                )

        except Exception as error:
            Jobs.update(job, status=JobStatus.ERROR, status_text=str(error))
            raise error

        Jobs.update(job, status=JobStatus.FINISHED)

    @staticmethod
    def _assert_restorable(
        snapshot: Snapshot, strategy=RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE
    ) -> None:
        service = ServiceManager.get_service_by_id(snapshot.service_name)
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
        folders = service.get_folders_to_back_up()

        Backups.provider().backupper.restore_from_backup(
            snapshot_id,
            folders,
            verify=verify,
        )

    # Snapshots

    @staticmethod
    def get_snapshots(service: Service) -> List[Snapshot]:
        """Returns all snapshots for a given service"""
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
        """Returns all snapshots"""
        # When we refresh our cache:
        # 1. Manually
        # 2. On timer
        # 3. On new snapshot
        # 4. On snapshot deletion

        return Storage.get_cached_snapshots()

    @staticmethod
    def get_snapshot_by_id(snapshot_id: str) -> Optional[Snapshot]:
        """Returns a backup snapshot by its id"""
        snap = Storage.get_cached_snapshot_by_id(snapshot_id)
        if snap is not None:
            return snap

        # Possibly our cache entry got invalidated, let's try one more time
        Backups.force_snapshot_cache_reload()
        snap = Storage.get_cached_snapshot_by_id(snapshot_id)

        return snap

    @staticmethod
    def forget_snapshots(snapshots: List[Snapshot]) -> None:
        """
        Deletes a batch of snapshots from the repo and syncs cache
        Optimized
        """
        ids = [snapshot.id for snapshot in snapshots]
        Backups.provider().backupper.forget_snapshots(ids)

        Backups.force_snapshot_cache_reload()

    @staticmethod
    def forget_snapshot(snapshot: Snapshot) -> None:
        """Deletes a snapshot from the repo and from cache"""
        Backups.forget_snapshots([snapshot])

    @staticmethod
    def forget_all_snapshots():
        """
        Mark all snapshots we have made for deletion and make them inaccessible
        (this is done by cloud, we only issue a command)
        """
        Backups.forget_snapshots(Backups.get_all_snapshots())

    @staticmethod
    def force_snapshot_cache_reload() -> None:
        """
        Forces a reload of the snapshot cache.

        This may be an expensive operation, so use it wisely.
        User pays for the API calls.
        """
        upstream_snapshots = Backups.provider().backupper.get_snapshots()
        Storage.invalidate_snapshot_storage()
        for snapshot in upstream_snapshots:
            Storage.cache_snapshot(snapshot)

    @staticmethod
    def snapshot_restored_size(snapshot_id: str) -> int:
        """Returns the size of the snapshot"""
        return Backups.provider().backupper.restored_size(
            snapshot_id,
        )

    @staticmethod
    def _on_new_snapshot_created(service_id: str, snapshot: Snapshot) -> None:
        """What do we do with a snapshot that is just made?"""
        # non-expiring timestamp of the last
        Storage.store_last_timestamp(service_id, snapshot)
        Backups.force_snapshot_cache_reload()

    # Autobackup

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
    def disable_all_autobackup() -> None:
        """
        Disables all automatic backing up,
        but does not change per-service settings
        """
        Storage.delete_backup_period()

    @staticmethod
    def is_time_to_backup(time: datetime) -> bool:
        """
        Intended as a time validator for huey cron scheduler
        of automatic backups
        """

        return Backups.services_to_back_up(time) != []

    @staticmethod
    def services_to_back_up(time: datetime) -> List[Service]:
        """Returns a list of services that should be backed up at a given time"""
        return [
            service
            for service in ServiceManager.get_all_services()
            if Backups.is_time_to_backup_service(service, time)
        ]

    @staticmethod
    def get_last_backed_up(service: Service) -> Optional[datetime]:
        """Get a timezone-aware time of the last backup of a service"""
        return Storage.get_last_backup_time(service.get_id())

    @staticmethod
    def get_last_backup_error_time(service: Service) -> Optional[datetime]:
        """Get a timezone-aware time of the last backup of a service"""
        job = get_backup_fail(service)
        if job is not None:
            datetime_created = job.created_at
            if datetime_created.tzinfo is None:
                # assume it is in localtime
                offset = timedelta(seconds=time.localtime().tm_gmtoff)
                datetime_created = datetime_created - offset
                return datetime.combine(
                    datetime_created.date(), datetime_created.time(), timezone.utc
                )
            return datetime_created
        return None

    @staticmethod
    def is_time_to_backup_service(service: Service, time: datetime):
        """Returns True if it is time to back up a service"""
        period = Backups.autobackup_period_minutes()
        if period is None:
            return False

        if not service.is_enabled():
            return False
        if not service.can_be_backed_up():
            return False

        last_error = Backups.get_last_backup_error_time(service)

        if last_error is not None:
            if time < last_error + timedelta(seconds=AUTOBACKUP_JOB_EXPIRATION_SECONDS):
                return False

        last_backup = Backups.get_last_backed_up(service)

        # Queue a backup immediately if there are no previous backups
        if last_backup is None:
            return True

        if time > last_backup + timedelta(minutes=period):
            return True

        return False

    # Helpers

    @staticmethod
    def space_usable_for_service(service: Service) -> int:
        """
        Returns the amount of space available on the volume the given
        service is located on.
        """
        folders = service.get_folders_to_back_up()
        if folders == []:
            raise ValueError("unallocated service", service.get_id())

        # We assume all folders of one service live at the same volume
        example_folder = folders[0]
        if exists(example_folder):
            fs_info = statvfs(example_folder)
            usable_bytes = fs_info.f_frsize * fs_info.f_bavail
        else:
            # Look at the block device as it is written in settings
            label = service.get_drive()
            device = BlockDevices().get_block_device(label)
            if device is None:
                raise ValueError("nonexistent drive ", label, " for ", service.get_id())
            usable_bytes = int(device.fsavail)

        return usable_bytes

    @staticmethod
    def set_localfile_repo(file_path: str):
        """Used by tests to set a local folder as a backup repo"""
        # pylint: disable-next=invalid-name
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
        """
        Checks if a service is dead and can be safely restored from a snapshot.
        """
        if service.get_status() not in [
            ServiceStatus.INACTIVE,
            ServiceStatus.FAILED,
        ]:
            raise NotDeadError(service)

    @staticmethod
    def is_same_slice(snap1: Snapshot, snap2: Snapshot) -> bool:
        # Determines if the snaps were made roughly in the same time period

        period_minutes = Backups.autobackup_period_minutes()
        # Autobackups are not guaranteed to be enabled during restore.
        # If they are not, period will be none
        # We ASSUME that picking latest snap of the same day is safe enough
        # But it is potentlially problematic and is better done with metadata I think.
        if period_minutes is None:
            period_minutes = 24 * 60

        if snap1.created_at > snap2.created_at + timedelta(minutes=period_minutes):
            return False
        if snap1.created_at < snap2.created_at - timedelta(minutes=period_minutes):
            return False
        return True

    @staticmethod
    def last_backup_slice() -> List[Snapshot]:
        """
        Guarantees that the slice is valid, ie, it has an api snapshot too
        Or empty
        """
        slice: List[Snapshot] = []

        # We need snapshots that were made around the same time.
        # And we need to be sure that api snap is in there
        # That's why we form the slice around api snap
        api_snaps = Backups.get_snapshots(ServiceManager())
        if api_snaps == []:
            return []

        api_snaps.sort(key=lambda x: x.created_at, reverse=True)
        api_snap = api_snaps[0]  # pick the latest one

        for service in ServiceManager.get_all_services():
            if isinstance(service, ServiceManager):
                continue
            snaps = Backups.get_snapshots(service)
            snaps.sort(key=lambda x: x.created_at, reverse=True)
            for snap in snaps:
                if Backups.is_same_slice(snap, api_snap):
                    slice.append(snap)
                break
        slice.append(api_snap)

        return slice
