"""
A task to start the system upgrade or rebuild by starting a systemd unit.
After starting, track the status of the systemd unit and update the Job
status accordingly.
"""
import subprocess
import time
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.jobs import JobStatus, Jobs, Job
from datetime import datetime

START_TIMEOUT = 60 * 5
START_INTERVAL = 1
RUN_TIMEOUT = 60 * 60
RUN_INTERVAL = 5


@huey.task()
def rebuild_system_task(job: Job, upgrade: bool = False):
    """Rebuild the system"""
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
        # Get current time to handle timeout
        start_time = datetime.now()
        # Wait for the systemd unit to start
        while True:
            try:
                status = subprocess.run(
                    ["systemctl", "is-active", unit_name],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if status.stdout.strip() == "active":
                    break
                if (datetime.now() - start_time).total_seconds() > START_TIMEOUT:
                    Jobs.update(
                        job=job,
                        status=JobStatus.ERROR,
                        error="System rebuild timed out.",
                    )
                    return
                time.sleep(START_INTERVAL)
            except subprocess.CalledProcessError:
                pass
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Rebuilding the system...",
        )
        # Wait for the systemd unit to finish
        while True:
            try:
                status = subprocess.run(
                    ["systemctl", "is-active", unit_name],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if status.stdout.strip() == "inactive":
                    Jobs.update(
                        job=job,
                        status=JobStatus.FINISHED,
                        result="System rebuilt.",
                        progress=100,
                    )
                    break
                elif status.stdout.strip() == "failed":
                    Jobs.update(
                        job=job,
                        status=JobStatus.ERROR,
                        error="System rebuild failed.",
                    )
                    break
                elif status.stdout.strip() == "active":
                    log_line = subprocess.run(
                        [
                            "journalctl",
                            "-u",
                            unit_name,
                            "-n",
                            "1",
                            "-o",
                            "cat",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    Jobs.update(
                        job=job,
                        status=JobStatus.RUNNING,
                        status_text=f"{log_line}",
                    )
            except subprocess.CalledProcessError:
                pass
            if (datetime.now() - start_time).total_seconds() > RUN_TIMEOUT:
                Jobs.update(
                    job=job,
                    status=JobStatus.ERROR,
                    error="System rebuild timed out.",
                )
                break
            time.sleep(RUN_INTERVAL)

    except subprocess.CalledProcessError as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=str(e),
        )
