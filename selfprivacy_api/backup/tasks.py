"""
The tasks module contains the worker tasks that are used to back up and restore
"""
from datetime import datetime, timezone

from selfprivacy_api.graphql.common_types.backup import (
    RestoreStrategy,
    BackupReason,
)

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.utils.huey import huey
from huey import crontab

from selfprivacy_api.services.service import Service
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.backup import Backups
from selfprivacy_api.jobs import Jobs, JobStatus, Job


SNAPSHOT_CACHE_TTL_HOURS = 6


def validate_datetime(dt: datetime) -> bool:
    """
    Validates that it is time to back up.
    Also ensures that the timezone-aware time is used.
    """
    if dt.tzinfo is None:
        return Backups.is_time_to_backup(dt.replace(tzinfo=timezone.utc))
    return Backups.is_time_to_backup(dt)


# huey tasks need to return something
@huey.task()
def start_backup(service_id: str, reason: BackupReason = BackupReason.EXPLICIT) -> bool:
    """
    The worker task that starts the backup process.
    """
    service = get_service_by_id(service_id)
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


def do_autobackup():
    """
    Body of autobackup task, broken out to test it
    For some reason, we cannot launch periodic huey tasks
    inside tests
    """
    time = datetime.utcnow().replace(tzinfo=timezone.utc)
    for service in Backups.services_to_back_up(time):
        handle = start_backup(service.get_id(), BackupReason.AUTO)
        # To be on safe side, we do not do it in parallel
        handle(blocking=True)


@huey.periodic_task(validate_datetime=validate_datetime)
def automatic_backup() -> bool:
    """
    The worker periodic task that starts the automatic backup process.
    """
    do_autobackup()
    return True


@huey.periodic_task(crontab(hour="*/" + str(SNAPSHOT_CACHE_TTL_HOURS)))
def reload_snapshot_cache():
    Backups.force_snapshot_cache_reload()
