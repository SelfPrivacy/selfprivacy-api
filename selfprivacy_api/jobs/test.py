import time
from selfprivacy_api.utils.huey import Huey
from selfprivacy_api.jobs import JobStatus, Jobs

huey = Huey()


@huey.task()
def test_job():
    job = Jobs.get_instance().add(
        name="Test job",
        description="This is a test job.",
        status=JobStatus.CREATED,
        status_text="",
        progress=0,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Performing pre-move checks...",
        progress=5,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Performing pre-move checks...",
        progress=10,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Performing pre-move checks...",
        progress=15,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Performing pre-move checks...",
        progress=20,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.RUNNING,
        status_text="Performing pre-move checks...",
        progress=25,
    )
    time.sleep(5)
    Jobs.get_instance().update(
        job=job,
        status=JobStatus.FINISHED,
        status_text="Job finished.",
        progress=100,
    )
