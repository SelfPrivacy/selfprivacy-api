import re
import subprocess
from typing import Tuple, Iterable, Optional
import gettext

from selfprivacy_api.utils.huey import huey
from selfprivacy_api.utils.localization import TranslateSystemMessage as t

from selfprivacy_api.jobs import JobStatus, Jobs, Job

_ = gettext.gettext


class ShellException(Exception):
    """Shell-related errors"""

    def __init__(self, error: Optional[str] = None) -> None:
        self.error = error

    def get_error_message(self, locale: str) -> str:
        return (
            t.translate(text=self.error, locale=locale)
            if self.error
            else t.translate(text=_("Shell-related error"), locale=locale)
        )


COMPLETED_WITH_ERROR = _("Error occurred, please report this to the support chat.")
RESULT_WAS_NOT_FOUND_ERROR = _(
    "We are sorry, garbage collection result was not found. "
    "Nix returned gibberish output, please report this to the support chat."
)
CLEAR_COMPLETED = _("Garbage collection completed.")


def delete_old_gens_and_return_dead_report() -> str:
    subprocess.run(
        [
            "nix-env",
            "-p",
            "/nix/var/nix/profiles/system",
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
        raise ShellException(error=RESULT_WAS_NOT_FOUND_ERROR)

    else:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            status_text=CLEAR_COMPLETED,
            result=f"{match.group(0)} {_("have been cleared")}",
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
                    status_text=_("Cleaning..."),
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
        status_text=_("Calculate the number of dead packages..."),
    )

    dead_packages, package_equal_to_percent = get_dead_packages(
        delete_old_gens_and_return_dead_report()
    )

    if dead_packages == 0:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            status_text=_("Nothing to clear"),
            result=_("System is clear"),
        )
        return True

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=_("Found %(dead_packages)s packages to remove!")
        % {"dead_packages": dead_packages},
    )

    stream = run_nix_collect_garbage()
    try:
        process_stream(job, stream, dead_packages)
    except ShellException:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=COMPLETED_WITH_ERROR,
            error=RESULT_WAS_NOT_FOUND_ERROR,
        )


def start_nix_collect_garbage() -> Job:
    job = Jobs.add(
        type_id="maintenance.collect_nix_garbage",
        name=_("Collect garbage"),
        description=_("Cleaning up unused packages"),
    )

    calculate_and_clear_dead_paths(job=job)

    return job
