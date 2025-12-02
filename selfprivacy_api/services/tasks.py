from huey import crontab

from selfprivacy_api.services import Service
from selfprivacy_api.services.suggested import SuggestedServices
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.utils.huey import huey, huey_async_helper
from selfprivacy_api.jobs import Job, Jobs, JobStatus

SUGGESTED_SERVICES_SYNC_EVERY_HOURS = 12


@huey.periodic_task(
    crontab(hour="*/" + str(SUGGESTED_SERVICES_SYNC_EVERY_HOURS), minute="0")
)
def suggested_services_sync():
    huey_async_helper.run_async(SuggestedServices.sync())


@huey.task()
def move_service(service: Service, new_volume: BlockDevice, job: Job) -> bool:
    """
    Move service's folders to new physical volume
    Does not raise exceptions (we cannot handle exceptions from tasks).
    Reports all errors via job.
    """
    try:
        huey_async_helper.run_async(service.move_to_volume(new_volume, job))
    except Exception as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            error=type(e).__name__ + " " + str(e),
        )
    return True
