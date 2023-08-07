import re
import subprocess

from selfprivacy_api.utils.huey import huey

from selfprivacy_api.jobs import JobStatus, Jobs, Job


COMPLETED_WITH_ERROR = "Completed with an error"
RESULT_WAS_NOT_FOUND_ERROR = "We are sorry, result was not found :("
CLEAR_COMPLETED = "Cleaning completed."


def run_nix_store_print_dead():
    subprocess.run(["nix-env", "-p", "/nix/var/nix/profiles/system", "--delete-generations old"], check=False)

    return subprocess.check_output(["nix-store", "--gc", "--print-dead"]).decode(
        "utf-8"
    )


def run_nix_collect_garbage():
    return subprocess.Popen(
        ["nix-store", "--gc"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout


def parse_line(line):
    pattern = re.compile(r"[+-]?\d+\.\d+ \w+(?= freed)")
    match = re.search(pattern, line)

    if match is None:
        return (
            JobStatus.FINISHED,
            100,
            COMPLETED_WITH_ERROR,
            RESULT_WAS_NOT_FOUND_ERROR,
        )

    else:
        return (
            JobStatus.FINISHED,
            100,
            CLEAR_COMPLETED,
            f"{match.group(0)} have been cleared",
        )


def stream_process(job, stream, total_dead_packages):
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
            status = parse_line(line)
            Jobs.update(
                job=job,
                status=status[0],
                progress=status[1],
                status_text=status[2],
                result=status[3],
            )


def get_dead_packages(output):
    dead = len(re.findall("/nix/store/", output))
    percent = 0
    if dead != 0:
        percent = 100 / dead
    return dead, percent


@huey.task()
def calculate_and_clear_dead_packages(job: Jobs):
    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text="Calculate the number of dead packages...",
    )

    dead_packages, package_equal_to_percent = get_dead_packages(
        run_nix_store_print_dead()
    )

    if dead_packages == 0:
        Jobs.update(
            job=job,
            status=JobStatus.FINISHED,
            progress=100,
            status_text="Nothing to clear",
            result="System is clear",
        )
        return

    Jobs.update(
        job=job,
        status=JobStatus.RUNNING,
        progress=0,
        status_text=f"Found {dead_packages} packages to remove!",
    )

    stream_process(job, run_nix_collect_garbage(), package_equal_to_percent)


def start_nix_collect_garbage() -> Job:
    job = Jobs.add(
        type_id="maintenance.collect_nix_garbage",
        name="Collect garbage",
        description="Cleaning up unused packages",
    )
    calculate_and_clear_dead_packages(job=job)
    return job
