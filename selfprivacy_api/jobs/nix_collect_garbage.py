import re
import subprocess

from selfprivacy_api.jobs import JobStatus, Jobs


COMPLETED_WITH_ERROR = "Completed with an error"
RESULT_WAAS_NOT_FOUND_ERROR = "We are sorry, result was not found :("
CLEAR_COMPLETED = "Сleaning completed."


def run_nix_store_print_dead():
    return subprocess.check_output(["nix-store", "--gc", "--print-dead"]).decode(
        "utf-8"
    )


def run_nix_collect_garbage():
    return subprocess.Popen(
        ["nix-collect-garbage", "-d"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout


def set_job_status_wrapper(Jobs, job):
    def set_job_status(status, progress, status_text, result="Default result"):
        Jobs.update(
            job=job,
            status=status,
            progress=progress,
            status_text=status_text,
            result=result,
        )

    return set_job_status


def parse_line(line):
    pattern = re.compile(r"[+-]?\d+\.\d+ \w+(?= freed)")
    match = re.search(
        pattern,
        line,
    )

    if match is None:
        return (
            JobStatus.FINISHED,
            100,
            COMPLETED_WITH_ERROR,
            RESULT_WAAS_NOT_FOUND_ERROR,
        )

    else:
        return (
            JobStatus.FINISHED,
            100,
            CLEAR_COMPLETED,
            f"{match.group(0)} have been cleared",
        )


def stream_process(
    stream,
    package_equal_to_percent,
    set_job_status,
):
    percent = 0

    for line in stream:
        if "deleting '/nix/store/" in line:
            percent += package_equal_to_percent

            set_job_status(
                status=JobStatus.RUNNING,
                progress=int(percent),
                status_text="Сleaning...",
            )

        elif "store paths deleted," in line:
            status = parse_line(line)
            set_job_status(
                status=status[0],
                progress=status[1],
                status_text=status[2],
                result=status[3],
            )


def get_dead_packages(output):
    dead = len(re.findall("/nix/store/", output))
    percent = None
    if dead != 0:
        percent = 100 / dead
    return dead, percent


def nix_collect_garbage(
    job,
    jobs=Jobs,
    run_nix_store=run_nix_store_print_dead,
    run_nix_collect=run_nix_collect_garbage,
    set_job_status=None,
):  # innocent as a pure function
    set_job_status = set_job_status or set_job_status_wrapper(jobs, job)

    set_job_status(
        status=JobStatus.RUNNING,
        progress=0,
        status_text="Сalculate the number of dead packages...",
    )

    dead_packages, package_equal_to_percent = get_dead_packages(run_nix_store())

    if dead_packages == 0:
        set_job_status(
            status=JobStatus.FINISHED,
            progress=100,
            status_text="Nothing to clear",
            result="System is clear",
        )
        return

    set_job_status(
        status=JobStatus.RUNNING,
        progress=0,
        status_text=f"Found {dead_packages} packages to remove!",
    )

    stream_process(run_nix_collect(), package_equal_to_percent, set_job_status)
