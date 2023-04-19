from datetime import datetime

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.services.service import Service
from selfprivacy_api.backup import Backups


def validate_datetime(dt: datetime):
    # dt = datetime.now(timezone.utc)
    if dt.timetz is None:
        raise ValueError(
            """
            huey passed in the timezone-unaware time! 
            Post it in support chat or maybe try uncommenting a line above
            """
        )
    return Backups.is_time_to_backup(dt)


# huey tasks need to return something
@huey.task()
def start_backup(service: Service) -> bool:
    Backups.back_up(service)
    return True


@huey.task()
def restore_snapshot(snapshot: Snapshot) -> bool:
    Backups.restore_snapshot(snapshot)
    return True


@huey.periodic_task(validate_datetime=validate_datetime)
def automatic_backup():
    time = datetime.now()
    for service in Backups.services_to_back_up(time):
        start_backup(service)
