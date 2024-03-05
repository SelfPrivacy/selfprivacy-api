"""Generic handler for moving services"""

from __future__ import annotations
import shutil
from typing import List

from selfprivacy_api.jobs import Job, report_progress
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.owned_path import Bind


class MoveError(Exception):
    """Move of the data has failed"""


def check_volume(volume: BlockDevice, space_needed: int) -> None:
    # Check if there is enough space on the new volume
    if int(volume.fsavail) < space_needed:
        raise MoveError("Not enough space on the new volume.")

    # Make sure the volume is mounted
    if not volume.is_root() and f"/volumes/{volume.name}" not in volume.mountpoints:
        raise MoveError("Volume is not mounted.")


def check_binds(volume_name: str, binds: List[Bind]) -> None:
    # Make sure current actual directory exists and if its user and group are correct
    for bind in binds:
        bind.validate()


def unbind_folders(owned_folders: List[Bind]) -> None:
    for folder in owned_folders:
        folder.unbind()


# May be moved into Bind
def move_data_to_volume(
    binds: List[Bind],
    new_volume: BlockDevice,
    job: Job,
) -> List[Bind]:
    current_progress = job.progress
    if current_progress is None:
        current_progress = 0

    progress_per_folder = 50 // len(binds)
    for bind in binds:
        old_location = bind.location_at_volume()
        bind.drive = new_volume
        new_location = bind.location_at_volume()

        try:
            shutil.move(old_location, new_location)
        except Exception as error:
            raise MoveError(
                f"could not move {old_location} to {new_location} : {str(error)}"
            ) from error

        progress = current_progress + progress_per_folder
        report_progress(progress, job, "Moving data to new volume...")
    return binds


def ensure_folder_ownership(folders: List[Bind]) -> None:
    for folder in folders:
        folder.ensure_ownership()


def bind_folders(folders: List[Bind]):
    for folder in folders:
        folder.bind()
