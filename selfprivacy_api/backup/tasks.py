"""
The tasks module contains the worker tasks that are used to back up and restore
"""
from datetime import datetime, timezone

from selfprivacy_api.graphql.common_types.backup import RestoreStrategy

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.services.service import Service
from selfprivacy_api.backup import Backups


def validate_datetime(dt: datetime) -> bool:
    """
    Validates that the datetime passed in is timezone-aware.
    """
    if dt.tzinfo is None:
        return Backups.is_time_to_backup(dt.replace(tzinfo=timezone.utc))
    return Backups.is_time_to_backup(dt)


# huey tasks need to return something
@huey.task()
def start_backup(service: Service) -> bool:
    """
    The worker task that starts the backup process.
    """
    Backups.back_up(service)
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


@huey.periodic_task(validate_datetime=validate_datetime)
def automatic_backup():
    """
    The worker periodic task that starts the automatic backup process.
    """
    time = datetime.utcnow().replace(tzinfo=timezone.utc)
    for service in Backups.services_to_back_up(time):
        start_backup(service)
