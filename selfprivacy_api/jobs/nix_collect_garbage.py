import re
import subprocess
from typing import Tuple, Iterable

from selfprivacy_api.utils.huey import huey

from selfprivacy_api.jobs import JobStatus, Jobs, Job


class ShellException(Exception):
    """Shell-related errors"""


COMPLETED_WITH_ERROR = "Error occurred, please report this to the support chat."
RESULT_WAS_NOT_FOUND_ERROR = (
    "We are sorry, garbage collection result was not found. "
    "Something went wrong, please report this to the support chat."
)
CLEAR_COMPLETED = "Garbage collection completed."


def delete_old_gens_and_return_dead_report() -> str:
    subprocess.run(
        [
            "nix-env",
            "-p", "/nix/var/nix/profiles/system",
            "--delete-generations",
            "old",
        ],
        check=False,
    )

    result = subprocess.check_output(["nix-store", "--gc", "--print-dead"]).decode(
        "utf-8"
    )

    return " " if result is None else result


def run_nix_collect_garbage() -> Iterable[bytes]:
    process = subprocess.Popen(
        ["nix-store", "--gc"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return process.stdout if process.stdout else iter([])


def parse_line(job: Job, line: str) -> Job:
    """
    We parse the string for the presence of a final line,
    with the final amount of space cleared.
    Simply put, we're just looking for a similar string:
    "1537 store paths deleted, 339.84 MiB freed".
    """
    pattern = re.compile(r"[+-]?\d+\.\d+ \w+(?= freed)")
    match = re.search(pattern, line)

    if match is None:
        raise ShellException("nix returned gibberish output")

    else:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            status_text=CLEAR_COMPLETED,
            result=f"{match.group(0)} have been cleared",
        )
    return job


def process_stream(job: Job, stream: Iterable[bytes], total_dead_packages: int) -> None:
    completed_packages = 0
    prev_progress = 0

    for line in stream:
        line = line.decode("utf-8")

        if "deleting '/nix/store/" in line:
            completed_packages += 1
            percent = int((completed_packages / total_dead_packages) * 100)

            if percent - prev_progress >= 5:
                Jobs.update(
                    job=job,
                    status=JobStatus.RUNNING,
                    progress=percent,
                    status_text="Cleaning...",
                )
                prev_progress = percent

        elif "store paths deleted," in line:
            parse_line(job, line)


def get_dead_packages(output) -> Tuple[int, float]:
    dead = len(re.findall("/nix/store/", output))
    percent = 0
    if dead != 0:
        percent = 100 / dead
    return dead, percent


@huey.task()
def calculate_and_clear_dead_paths(job: Job):
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text="Calculate the number of dead packages...",
    )

    dead_packages, package_equal_to_percent = get_dead_packages(
        delete_old_gens_and_return_dead_report()
    )

    if dead_packages == 0:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            status_text="Nothing to clear",
            result="System is clear",
        )
        return True

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=f"Found {dead_packages} packages to remove!",
    )

    stream = run_nix_collect_garbage()
    try:
        process_stream(job, stream, dead_packages)
    except ShellException as error:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=COMPLETED_WITH_ERROR,
            error=RESULT_WAS_NOT_FOUND_ERROR,
        )


def start_nix_collect_garbage() -> Job:
    job = Jobs.add(
        type_id="maintenance.collect_nix_garbage",
        name="Collect garbage",
        description="Cleaning up unused packages",
    )

    calculate_and_clear_dead_paths(job=job)

    return job
