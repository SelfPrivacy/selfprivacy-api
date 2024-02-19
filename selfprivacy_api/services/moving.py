"""Generic handler for moving services"""

from __future__ import annotations
import subprocess
import pathlib
import shutil
from typing import List

from selfprivacy_api.jobs import Job, report_progress
from selfprivacy_api.utils.block_devices import BlockDevice
from selfprivacy_api.services.owned_path import OwnedPath


class MoveError(Exception):
    """Move failed"""


def get_foldername(p: OwnedPath) -> str:
    return p.path.split("/")[-1]


def location_at_volume(binding_path: OwnedPath, volume_name: str):
    return f"/volumes/{volume_name}/{get_foldername(binding_path)}"


def check_volume(volume: BlockDevice, space_needed: int) -> None:
    # Check if there is enough space on the new volume
    if int(volume.fsavail) < space_needed:
        raise MoveError("Not enough space on the new volume.")

    # Make sure the volume is mounted
    if not volume.is_root() and f"/volumes/{volume.name}" not in volume.mountpoints:
        raise MoveError("Volume is not mounted.")


def check_folders(volume_name: str, folders: List[OwnedPath]) -> None:
    # Make sure current actual directory exists and if its user and group are correct
    for folder in folders:
        path = pathlib.Path(location_at_volume(folder, volume_name))

        if not path.exists():
            raise MoveError(f"directory {path} is not found.")
        if not path.is_dir():
            raise MoveError(f"{path} is not a directory.")
        if path.owner() != folder.owner:
            raise MoveError(f"{path} is not owned by {folder.owner}.")


def unbind_folders(owned_folders: List[OwnedPath]) -> None:
    for folder in owned_folders:
        try:
            subprocess.run(
                ["umount", folder.path],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise MoveError(f"Unable to unmount folder {folder.path}.")


def move_folders_to_volume(
    folders: List[OwnedPath],
    old_volume_name: str,  # TODO: pass an actual validated block device
    new_volume: BlockDevice,
    job: Job,
) -> None:
    current_progress = job.progress
    if current_progress is None:
        current_progress = 0

    progress_per_folder = 50 // len(folders)
    for folder in folders:
        shutil.move(
            location_at_volume(folder, old_volume_name),
            location_at_volume(folder, new_volume.name),
        )
        progress = current_progress + progress_per_folder
        report_progress(progress, job, "Moving data to new volume...")


def ensure_folder_ownership(folders: List[OwnedPath], volume: BlockDevice) -> None:
    for folder in folders:
        true_location = location_at_volume(folder, volume.name)
        try:
            subprocess.run(
                [
                    "chown",
                    "-R",
                    f"{folder.owner}:{folder.group}",
                    # Could we just chown the binded location instead?
                    true_location,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.output)
            error_message = (
                f"Unable to set ownership of {true_location} :{error.output}"
            )
            raise MoveError(error_message)


def bind_folders(folders: List[OwnedPath], volume: BlockDevice) -> None:
    for folder in folders:
        try:
            subprocess.run(
                [
                    "mount",
                    "--bind",
                    location_at_volume(folder, volume.name),
                    folder.path,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.output)
            raise MoveError(f"Unable to mount new volume:{error.output}")
