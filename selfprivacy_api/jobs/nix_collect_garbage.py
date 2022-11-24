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
        status_text="Start cleaning.",
    )

    output = subprocess.check_output(["nix-collect-garbage", "-d"])

    pat = re.compile(r"linking saves ([+-]?\d+\.\d+ \w+).+?([+-]?\d+\.\d+ \w+) freed")
    match = re.search(
        pat,
        output,
    )

    Jobs.update(
        job=job,
        status=JobStatus.FINISHED,
        progress=100,
        status_text="Сleaning completed.",
        result=f"Currently hard linking saves {match.group(1)}, {match.group(2)} freed",
    )
