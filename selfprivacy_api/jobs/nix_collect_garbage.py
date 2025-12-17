import logging
import gettext
from typing import Any, Tuple, Iterable
import re
import subprocess
from textwrap import dedent

from selfprivacy_api.utils.huey import huey
from selfprivacy_api.utils.localization import (
    DEFAULT_LOCALE,
    TranslateSystemMessage as t,
)

from selfprivacy_api.jobs import JobStatus, Jobs, Job
from selfprivacy_api.utils.strings import REPORT_IT_TO_SUPPORT_CHATS

logger = logging.getLogger(__name__)

_ = gettext.gettext

CLEAR_NIX_STORAGE_COMMAND = ["nix-store", "--gc"]


class FailedToFindResult(Exception):
    def __init__(self, regex_pattern: str, command: str, data: str):
        self.regex_pattern = regex_pattern
        self.command = command
        self.data = data

        logger.error(self.get_error_message())

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Garbage collection result was not found.
                    The code analyzes the last line in the command output using a regular expression.
                    Simply put, we're just looking for a similar string: "1537 store paths deleted, 339.84 MiB freed".
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Command: %(command)s
                    Used regex pattern: %(regex_pattern)s
                    Last line: %(last_line)s
                    """
                )
            )
            % {
                "command": self.command,
                "regex_pattern": self.regex_pattern,
                "last_line": self.data,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )


class ShellException(Exception):
    """Shell command failed"""

    def __init__(self, command: str, output: Any, description: str):
        self.command = command
        self.description = description
        self.output = str(output)

    def get_error_message(self, locale: str = DEFAULT_LOCALE) -> str:
        return t.translate(
            text=_(
                dedent(
                    """
                    Shell command failed.
                    %(description)s
                    %(REPORT_IT_TO_SUPPORT_CHATS)s
                    Executed command: %(command)s
                    Output: %(output)s
                    """
                )
            )
            % {
                "command": self.command,
                "description": self.description,
                "output": self.output,
                "REPORT_IT_TO_SUPPORT_CHATS": REPORT_IT_TO_SUPPORT_CHATS,
            },
            locale=locale,
        )


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
def run_task(job: Job):
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
    process_stream(job, stream, dead_packages)


def nix_collect_garbage() -> Job:
    job = Jobs.add(
        type_id="maintenance.collect_nix_garbage",
        name=_("Collect garbage"),
        description=_("Cleaning up unused packages"),
    )

    try:
        run_task(job=job)
    except ShellException as error:
        error_message = (
            error.get_error_message()
            if getattr(error, "get_error_message", None)
            else str(error)
        )

        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=_("Garbage collection failed"),
            error=error_message,  # need to translate
        )

    return job
