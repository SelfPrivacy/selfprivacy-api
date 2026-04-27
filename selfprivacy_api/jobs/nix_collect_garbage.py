import gettext
import re
import subprocess
from typing import Iterable, Tuple

from selfprivacy_api.exceptions.system import FailedToFindResult, ShellException
from selfprivacy_api.jobs import Job, Jobs, JobStatus
from selfprivacy_api.utils.huey import huey

_ = gettext.gettext

CLEAR_NIX_STORAGE_COMMAND = ["nix-store", "--gc"]


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


def action_nix_collect_garbage() -> Iterable[bytes]:
    process = subprocess.Popen(
        CLEAR_NIX_STORAGE_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return process.stdout if process.stdout else iter([])


def parse_line(job: Job, line: str) -> Job:
    """
    The code analyzes the last line in the command output using a regular expression.
    Simply put, we're just looking for a similar string:
    "1537 store paths deleted, 339.84 MiB freed".
    """

    regex_pattern = r"[+-]?\d+\.\d+ \w+(?= freed)"
    match = re.search(re.compile(regex_pattern), line)

    if match is None:
        raise FailedToFindResult(
            regex_pattern=regex_pattern,
            data=line,
            command=" ".join(CLEAR_NIX_STORAGE_COMMAND),
            description=(
                "Garbage collection result was not found.\n"
                "The code analyzes the last line in the command output using a regular expression.\n"
                "Simply put, we're just looking for a similar string: "
                '"1537 store paths deleted, 339.84 MiB freed".'
            ),
        )

    else:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            status_text=_("Garbage collection completed."),
            result=_("%(size_in_megabytes)s have been cleared")
            % {"size_in_megabytes": match.group(0)},
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
def nix_collect_garbage_task(job: Job):
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

    stream = action_nix_collect_garbage()

    error_message = None
    try:
        process_stream(job, stream, dead_packages)
    except ShellException as error:
        error_message = str(error)
    except FailedToFindResult as error:
        error_message = error.get_error_message()

    if error_message is not None:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=_("Garbage collection failed"),
            error=error_message,  # need to translate
        )


def start_nix_collect_garbage() -> Job:
    job = Jobs.add(
        type_id="maintenance.collect_nix_garbage",
        name=_("Collect garbage"),
        description=_("Cleaning up unused packages"),
    )

    nix_collect_garbage_task(job=job)

    return job
