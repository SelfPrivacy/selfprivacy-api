"""
A task to start the system upgrade or rebuild by starting a systemd unit.
After starting, track the status of the systemd unit and update the Job
status accordingly.
"""

import asyncio
from systemd import journal
from selfprivacy_api.utils.huey import huey, huey_async_helper
from selfprivacy_api.jobs import JobStatus, Jobs, Job
from selfprivacy_api.utils.systemd import (
    start_unit,
    get_service_status,
    wait_for_unit_state,
    get_last_log_lines,
    ServiceStatus,
)

START_TIMEOUT = 60 * 5
RUN_TIMEOUT = 60 * 60


async def report_active_rebuild_log(job: Job, unit_name: str):
    j = journal.Reader()

    j.add_match(_SYSTEMD_UNIT=unit_name)
    j.seek_tail()
    j.get_previous()

    log_queue = asyncio.Queue()

    async def callback():
        if j.process() != journal.APPEND:
            return
        for entry in j:
            await log_queue.put(entry)

    asyncio.get_event_loop().add_reader(j, lambda: asyncio.ensure_future(callback()))

    try:
        while True:
            log_entry = await log_queue.get()
            Jobs.update(
                job=job,
                status=JobStatus.RUNNING,
                status_text=log_entry["MESSAGE"],
            )
    except asyncio.CancelledError:
        asyncio.get_event_loop().remove_reader(j)
        j.close()


async def rebuild_system(job: Job, upgrade: bool = False):
    """
    Broken out to allow calling it synchronously.
    We cannot just block until task is done because it will require a second worker
    Which we do not have
    """

    unit_name = "sp-nixos-upgrade.service" if upgrade else "sp-nixos-rebuild.service"
    try:
        await start_unit(unit_name)
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Starting the system rebuild...",
        )
        # Wait for the systemd unit to start
        try:
            async with asyncio.timeout(START_TIMEOUT):
                await wait_for_unit_state(unit_name, [ServiceStatus.ACTIVE])
        except asyncio.TimeoutError:
            log_lines = get_last_log_lines(unit_name, 10)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="System rebuild timed out. Last log lines:\n"
                + "\n".join(log_lines),
            )
            return
        Jobs.update(
            job=job,
            status=JobStatus.RUNNING,
            status_text="Rebuilding the system...",
        )
        # Wait for the systemd unit to finish
        try:
            log_task = asyncio.create_task(report_active_rebuild_log(job, unit_name))

            async with asyncio.timeout(RUN_TIMEOUT):
                await wait_for_unit_state(
                    unit_name,
                    [
                        ServiceStatus.FAILED,
                        ServiceStatus.INACTIVE,
                    ],
                )

            log_task.cancel()
            await log_task

            status = await get_service_status(unit_name)

            if status == ServiceStatus.INACTIVE:
                Jobs.update(
                    job=job,
                    status=JobStatus.FINISHED,
                    result="System rebuilt.",
                    progress=100,
                )
            if status == ServiceStatus.FAILED:
                log_lines = get_last_log_lines(unit_name, 10)
                Jobs.update(
                    job=job,
                    status=JobStatus.ERROR,
                    error="System rebuild failed. Last log lines:\n"
                    + "\n".join(log_lines),
                )

        except asyncio.TimeoutError:
            log_task.cancel()
            await log_task

            log_lines = get_last_log_lines(unit_name, 10)
            Jobs.update(
                job=job,
                status=JobStatus.ERROR,
                error="System rebuild timed out. Last log lines:\n"
                + "\n".join(log_lines),
            )
            return

    except Exception as e:
        Jobs.update(
            job=job,
            status=JobStatus.ERROR,
            status_text=str(e),
        )


@huey.task()
def rebuild_system_task(job: Job, upgrade: bool = False):
    """Rebuild the system"""
    huey_async_helper.run_async(rebuild_system(job, upgrade))
