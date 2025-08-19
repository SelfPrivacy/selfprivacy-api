"""
The tasks module contains the worker tasks that are used to back up and restore
"""

from datetime import datetime, timezone
from typing import List

from selfprivacy_api.graphql.common_types.backup import (
    RestoreStrategy,
    BackupReason,
)

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.utils.huey import huey
from huey import crontab

from selfprivacy_api.services import ServiceManager, Service
from selfprivacy_api.backup import Backups
from selfprivacy_api.backup.jobs import add_autobackup_job
from selfprivacy_api.jobs import Jobs, JobStatus, Job
from selfprivacy_api.jobs.upgrade_system import rebuild_system
from selfprivacy_api.actions.system import add_rebuild_job


SNAPSHOT_CACHE_TTL_HOURS = 12


def validate_datetime(dt: datetime) -> bool:
    """
    Validates that it is time to back up.
    Also ensures that the timezone-aware time is used.
    """
    if dt.tzinfo is None:
        return Backups.is_time_to_backup(dt.replace(tzinfo=timezone.utc))
    return Backups.is_time_to_backup(dt)


def report_job_error(error: Exception, job: Job):
    Jobs.update(
        job,
        status=JobStatus.ERROR,
        error=type(error).__name__ + ": " + str(error),
    )


# huey tasks need to return something
@huey.task()
def start_backup(service_id: str, reason: BackupReason = BackupReason.EXPLICIT) -> bool:
    """
    The worker task that starts the backup process.
    """
    service = ServiceManager.get_service_by_id(service_id)
    if service is None:
        raise ValueError(f"No such service: {service_id}")
    Backups.back_up(service, reason)
    return True


@huey.task()
def prune_autobackup_snapshots(job: Job) -> bool:
    """
    Remove all autobackup snapshots that do not fit into quotas set
    """
    Jobs.update(job, JobStatus.RUNNING)
    try:
        Backups.prune_all_autosnaps()
    except Exception as e:
        Jobs.update(job, JobStatus.ERROR, error=type(e).__name__ + ":" + str(e))
        return False

    Jobs.update(job, JobStatus.FINISHED)
    return True


@huey.task()
def restore_snapshot(
    snapshot: Snapshot,
    strategy: RestoreStrategy = RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE,
) -> bool:
    """
    The worker task that starts the restore process.
    """
    Backups.restore_snapshot(snapshot, strategy)
    return True


@huey.task()
def full_restore(job: Job) -> bool:
    do_full_restore(job)
    return True


@huey.periodic_task(validate_datetime=validate_datetime)
def automatic_backup() -> None:
    """
    The worker periodic task that starts the automatic backup process.
    """
    do_autobackup()


@huey.task()
def total_backup(job: Job) -> bool:
    do_total_backup(job)
    return True


@huey.periodic_task(crontab(hour="*/" + str(SNAPSHOT_CACHE_TTL_HOURS), minute="0"))
def reload_snapshot_cache():
    Backups.force_snapshot_cache_reload()


def back_up_multiple(
    job: Job,
    services_to_back_up: List[Service],
    reason: BackupReason = BackupReason.EXPLICIT,
):
    if services_to_back_up == []:
        return

    progress_per_service = 100 // len(services_to_back_up)
    progress = 0
    Jobs.update(job, JobStatus.RUNNING, progress=progress)

    for service in services_to_back_up:
        try:
            Backups.back_up(service, reason)
        except Exception as error:
            report_job_error(error, job)
            raise error
        progress = progress + progress_per_service
        Jobs.update(job, JobStatus.RUNNING, progress=progress)


def do_total_backup(job: Job) -> None:
    """
    Body of total backup task, broken out to test it
    """
    back_up_multiple(job, ServiceManager.get_enabled_services())

    Jobs.update(job, JobStatus.FINISHED)


def do_autobackup() -> None:
    """
    Body of autobackup task, broken out to test it
    For some reason, we cannot launch periodic huey tasks
    inside tests
    """

    time = datetime.now(timezone.utc)
    backups_were_disabled = Backups.autobackup_period_minutes() is None

    if backups_were_disabled:
        # Temporarily enable autobackup
        Backups.set_autobackup_period_minutes(24 * 60)  # 1 day

    services_to_back_up = Backups.services_to_back_up(time)
    if not services_to_back_up:
        return
    job = add_autobackup_job(services_to_back_up)

    back_up_multiple(job, services_to_back_up, BackupReason.AUTO)

    if backups_were_disabled:
        Backups.set_autobackup_period_minutes(0)
    Jobs.update(job, JobStatus.FINISHED)
    # there is no point of returning the job
    # this code is called with a delay


def eligible_for_full_restoration(snap: Snapshot):
    service = ServiceManager.get_service_by_id(snap.service_name)
    if service is None:
        return False
    if service.is_enabled() is False:
        return False
    return True


def which_snapshots_to_full_restore() -> list[Snapshot]:
    autoslice = Backups.last_backup_slice()
    api_snapshot = None
    for snap in autoslice:
        if snap.service_name == ServiceManager.get_id():
            api_snapshot = snap
            autoslice.remove(snap)
    if api_snapshot is None:
        raise ValueError(
            "Cannot restore, no configuration snapshot found. This particular error should be unreachable"
        )

    snapshots_to_restore = [
        snap for snap in autoslice if eligible_for_full_restoration(snap)
    ]
    # API should be restored in the very end of the list because it requires rebuild right afterwards
    snapshots_to_restore.append(api_snapshot)
    return snapshots_to_restore


def do_full_restore(job: Job) -> None:
    """
    Body full restore task, a part of server migration.
    Broken out to test it independently from task infra
    """

    Jobs.update(
        job,
        JobStatus.RUNNING,
        status_text="Finding the last autobackup session",
        progress=0,
    )
    snapshots_to_restore = which_snapshots_to_full_restore()

    progress_per_service = 99 // len(snapshots_to_restore)
    progress = 0
    Jobs.update(job, JobStatus.RUNNING, progress=progress)

    for snap in snapshots_to_restore:
        try:
            Backups.restore_snapshot(snap)
        except Exception as error:
            report_job_error(error, job)
            return
        progress = progress + progress_per_service
        Jobs.update(
            job,
            JobStatus.RUNNING,
            status_text=f"restoring {snap.service_name}",
            progress=progress,
        )

    Jobs.update(job, JobStatus.RUNNING, status_text="rebuilding system", progress=99)

    # Adding a separate job to not confuse the user with jumping progress bar
    rebuild_job = add_rebuild_job()
    rebuild_system(rebuild_job)
    Jobs.update(job, JobStatus.FINISHED)
