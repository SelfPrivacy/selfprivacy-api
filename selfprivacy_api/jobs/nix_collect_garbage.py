import re
import subprocess

from selfprivacy_api.jobs import Job, JobStatus, Jobs
from selfprivacy_api.utils.huey import huey


def run_nix_store_print_dead():
    return subprocess.check_output(["nix-store", "--gc", "--print-dead"])


def run_nix_collect_garbage():
    return subprocess.Popen(
        ["nix-collect-garbage", "-d"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )


def parse_line(line, job: Job):
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


def stream_process(
    process,
    package_equal_to_percent,
    job: Job,
):
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
            parse_line(line, job)

    return go


@huey.task()
def nix_collect_garbage(
    job: Job,
    run_nix_store=run_nix_store_print_dead,
    run_nix_collect=run_nix_collect_garbage,
):  # innocent as a pure function

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text="Сalculate the number of dead packages...",
    )

    output = run_nix_store()

    dead_packages = len(re.findall("/nix/store/", output.decode("utf-8")))

    if dead_packages == 0:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            progress=100,
            status_text="Nothing to clear",
            result="System is clear",
        )

    package_equal_to_percent = 100 / dead_packages

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=f"Found {dead_packages} packages to remove!",
    )

    stream_process(run_nix_collect, package_equal_to_percent, job)
