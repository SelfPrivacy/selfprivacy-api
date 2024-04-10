"""
A task to start the system upgrade or rebuild by starting a systemd unit.
After starting, track the status of the systemd unit and update the Job
status accordingly.
"""
import subprocess
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.jobs import JobStatus, Jobs, Job
from selfprivacy_api.utils.waitloop import wait_until_true
from selfprivacy_api.utils.systemd import (
    get_service_status,
    get_last_log_lines,
    ServiceStatus,
)

START_TIMEOUT = 60 * 5
START_INTERVAL = 1
RUN_TIMEOUT = 60 * 60
RUN_INTERVAL = 5


def check_if_started(unit_name: str):
    """Check if the systemd unit has started"""
    try:
        status = get_service_status(unit_name)
        if status == ServiceStatus.ACTIVE:
            return True
        return False
    except subprocess.CalledProcessError:
        return False


def check_running_status(job: Job, unit_name: str):
    """Check if the systemd unit is running"""
    try:
        status = get_service_status(unit_name)
        if status == ServiceStatus.INACTIVE:
            Jobs.update(
                job=job,
                status=JobStatus.FINISHED,
                result="System rebuilt.",
                progress=100,
            )
            return True
        if status == ServiceStatus.FAILED:
            log_lines = get_last_log_lines(unit_name, 10)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="System rebuild failed. Last log lines:\n" + "\n".join(log_lines),
            )
            return True
        if status == ServiceStatus.ACTIVE:
            log_lines = get_last_log_lines(unit_name, 1)
            Jobs.update(
                job=job,
                status=JobStatus.RUNNING,
                status_text=log_lines[0] if len(log_lines) > 0 else "",
            )
            return False
        return False
    except subprocess.CalledProcessError:
        return False


def rebuild_system(job: Job, upgrade: bool = False):
    """
    Broken out to allow calling it synchronously.
    We cannot just block until task is done because it will require a second worker
    Which we do not have
    """

    unit_name = "sp-nixos-upgrade.service" if upgrade else "sp-nixos-rebuild.service"
    try:
        command = ["systemctl", "start", unit_name]
        subprocess.run(
            command,
            check=True,
            start_new_session=True,
            shell=False,
        )
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Starting the system rebuild...",
        )
        # Wait for the systemd unit to start
        try:
            wait_until_true(
                lambda: check_if_started(unit_name),
                timeout_sec=START_TIMEOUT,
                interval=START_INTERVAL,
            )
        except TimeoutError:
            log_lines = get_last_log_lines(unit_name, 10)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="System rebuild timed out. Last log lines:\n"
                + "\n".join(log_lines),
            )
            return
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Rebuilding the system...",
        )
        # Wait for the systemd unit to finish
        try:
            wait_until_true(
                lambda: check_running_status(job, unit_name),
                timeout_sec=RUN_TIMEOUT,
                interval=RUN_INTERVAL,
            )
        except TimeoutError:
            log_lines = get_last_log_lines(unit_name, 10)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="System rebuild timed out. Last log lines:\n"
                + "\n".join(log_lines),
            )
            return

    except subprocess.CalledProcessError as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=str(e),
        )


@huey.task()
def rebuild_system_task(job: Job, upgrade: bool = False):
    """Rebuild the system"""
    rebuild_system(job, upgrade)
