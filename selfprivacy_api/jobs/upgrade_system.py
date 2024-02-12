"""
A task to start the system upgrade or rebuild by starting a systemd unit.
After starting, track the status of the systemd unit and update the Job
status accordingly.
"""
import subprocess
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.jobs import JobStatus, Jobs, Job
import time


@huey.task()
def rebuild_system_task(job: Job, upgrade: bool = False):
    """Rebuild the system"""
    try:
        if upgrade:
            command = ["systemctl", "start", "sp-nixos-upgrade.service"]
        else:
            command = ["systemctl", "start", "sp-nixos-rebuild.service"]
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
        start_time = time.time()
        # Wait for the systemd unit to start
        while True:
            try:
                status = subprocess.run(
                    ["systemctl", "is-active", "selfprivacy-upgrade"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(status.stdout.strip())
                if status.stdout.strip() == "active":
                    break
                # Timeount after 5 minutes
                if time.time() - start_time > 300:
                    Jobs.update(
                        job=job,
                        status=JobStatus.ERROR,
                        error="System rebuild timed out.",
                    )
                    return
                time.sleep(1)
            except subprocess.CalledProcessError:
                pass
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Rebuilding the system...",
        )
        print("Rebuilding the system...")
        # Wait for the systemd unit to finish
        while True:
            try:
                status = subprocess.run(
                    ["systemctl", "is-active", "selfprivacy-upgrade"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print(status.stdout.strip())
                if status.stdout.strip() == "inactive":
                    Jobs.update(
                        job=job,
                        status=JobStatus.FINISHED,
                        result="System rebuilt.",
                        progress=100,
                    )
                elif status.stdout.strip() == "failed":
                    Jobs.update(
                        job=job,
                        status=JobStatus.ERROR,
                        error="System rebuild failed.",
                    )
                    break
                elif status.stdout.strip() == "active":
                    print("Geting a log line")
                    log_line = subprocess.run(
                        [
                            "journalctl",
                            "-u",
                            "selfprivacy-upgrade",
                            "-n",
                            "1",
                            "-o",
                            "cat",
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout.strip()
                    print(log_line)
                    Jobs.update(
                        job=job,
                        status=JobStatus.RUNNING,
                        status_text=f"Rebuilding the system... Latest log line: {log_line}",
                    )
                # Timeout of 60 minutes
                if time.time() - start_time > 3600:
                    Jobs.update(
                        job=job,
                        status=JobStatus.ERROR,
                        error="System rebuild timed out.",
                    )
                    break
                time.sleep(5)
            except subprocess.CalledProcessError:
                pass

    except subprocess.CalledProcessError as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=str(e),
        )
