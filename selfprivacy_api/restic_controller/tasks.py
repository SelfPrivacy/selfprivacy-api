"""Tasks for the restic controller."""
from huey import crontab
from huey.contrib.mini import MiniHuey
from . import ResticController, ResticStates

huey = MiniHuey()


@huey.task()
def init_restic():
    controller = ResticController()
    if controller.state == ResticStates.NOT_INITIALIZED:
        initialize_repository()


@huey.task()
def update_keys_from_userdata():
    controller = ResticController()
    controller.load_configuration()
    controller.write_rclone_config()
    initialize_repository()


# Check every morning at 5:00 AM
@huey.task(crontab(hour=5, minute=0))
def cron_load_snapshots():
    controller = ResticController()
    controller.load_snapshots()


# Check every morning at 5:00 AM
@huey.task()
def load_snapshots():
    controller = ResticController()
    controller.load_snapshots()
    if controller.state == ResticStates.NOT_INITIALIZED:
        load_snapshots.schedule(delay=120)


@huey.task()
def initialize_repository():
    controller = ResticController()
    if controller.state is not ResticStates.NO_KEY:
        controller.initialize_repository()
        load_snapshots()


@huey.task()
def fetch_backup_status():
    controller = ResticController()
    if controller.state is ResticStates.BACKING_UP:
        controller.check_progress()
        if controller.state is ResticStates.BACKING_UP:
            fetch_backup_status.schedule(delay=2)
        else:
            load_snapshots.schedule(delay=240)


@huey.task()
def start_backup():
    controller = ResticController()
    if controller.state is ResticStates.NOT_INITIALIZED:
        resp = initialize_repository()
        resp.get()
    controller.start_backup()
    fetch_backup_status.schedule(delay=3)


@huey.task()
def restore_from_backup(snapshot):
    controller = ResticController()
    controller.restore_from_backup(snapshot)
