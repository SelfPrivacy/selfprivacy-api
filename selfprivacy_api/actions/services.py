import gettext
import logging

from selfprivacy_api.exceptions.services import (
    ServiceNotFoundError,
    VolumeNotFoundError,
)
from selfprivacy_api.jobs import Job, Jobs
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.tasks import move_service as move_service_task
from selfprivacy_api.utils.block_devices import BlockDevices

logger = logging.getLogger(__name__)

_ = gettext.gettext


async def move_service(service_id: str, volume_name: str) -> Job:
    service = await ServiceManager.get_service_by_id(service_id)
    if service is None:
        raise ServiceNotFoundError(service_id=service_id)

    volume = BlockDevices().get_block_device_by_canonical_name(volume_name)
    if volume is None:
        raise VolumeNotFoundError(volume_name=volume_name)

    await service.assert_can_move(volume)

    job = Jobs.add(
        type_id=f"services.{service.get_id()}.move",
        name=_("Move %(service)s") % {"service": service.get_display_name()},
        description=_("Moving %(service)s data to %(volume)s")
        % {
            "service": service.get_display_name(),
            "volume": volume.get_display_name().lower(),
        },
    )

    move_service_task(service, volume, job)
    return job
