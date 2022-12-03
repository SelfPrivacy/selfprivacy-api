from time import sleep
import re
import subprocess

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.utils.huey import huey


@huey.task()
def nix_collect_garbage(job: Job):

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text="Сalculate the number of dead packages...",
    )

    output = subprocess.check_output(
        ["nix-store --gc --print-dead", "--gc", "--print-dead"]
    )

    dead_packages = len(re.findall("/nix/store/", output.decode("utf-8")))
    package_equal_to_percent = 100 / dead_packages

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=f"Found {dead_packages} packages to remove!",
    )

    def _parse_line(line):
        pattern = re.compile(r"[+-]?\d+\.\d+ \w+ freed")
        match = re.search(
            pattern,
            line,
        )

        if match is None:
            Jobs.update(
                job=job,
                status=JobStatus.FINISHED,
                progress=100,
                status_text="Completed with an error",
                result="We are sorry, result was not found :(",
            )

        else:
            Jobs.update(
                job=job,
                status=JobStatus.FINISHED,
                progress=100,
                status_text="Сleaning completed.",
                result=f"{match.group(0)} have been cleared",
            )

    def _stream_process(process):
        go = process.poll() is None
        percent = 0

        for line in process.stdout:
            if "deleting '/nix/store/" in line:
                percent += package_equal_to_percent

                Jobs.update(
                    job=job,
                    status=JobStatus.RUNNING,
                    progress=int(percent),
                    status_text="Сleaning...",
                )

            elif "store paths deleted," in line:
                _parse_line(line)

        return go

    process = subprocess.Popen(
        ["nix-collect-garbage", "-d"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    _stream_process(process)
