from selfprivacy_api.services import Service
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey
from selfprivacy_api.jobs import Job, Jobs, JobStatus


@huey.task()
def move_service(service: Service, new_volume: BlockDevice, job: Job) -> bool:
    """
    Move service's folders to new physical volume
    Does not raise exceptions (we cannot handle exceptions from tasks).
    Reports all errors via job.
    """
    try:
        service.move_to_volume(new_volume, job)
    except Exception as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=type(e).__name__ + " " + str(e),
        )
    return True
