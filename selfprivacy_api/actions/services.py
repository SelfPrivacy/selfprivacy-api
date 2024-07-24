from selfprivacy_api.utils.block_devices import BlockDevices
from selfprivacy_api.jobs import Jobs, Job

from selfprivacy_api.services import ServiceManager
from selfprivacy_api.services.tasks import move_service as move_service_task


class ServiceNotFoundError(Exception):
    pass


class VolumeNotFoundError(Exception):
    pass


def move_service(service_id: str, volume_name: str) -> Job:
    service = ServiceManager.get_service_by_id(service_id)
    if service is None:
        raise ServiceNotFoundError(f"No such service:{service_id}")

    volume = BlockDevices().get_block_device(volume_name)
    if volume is None:
        raise VolumeNotFoundError(f"No such volume:{volume_name}")

    service.assert_can_move(volume)

    job = Jobs.add(
        type_id=f"services.{service.get_id()}.move",
        name=f"Move {service.get_display_name()}",
        description=f"Moving {service.get_display_name()} data to {volume.get_display_name().lower()}",
    )

    move_service_task(service, volume, job)
    return job
