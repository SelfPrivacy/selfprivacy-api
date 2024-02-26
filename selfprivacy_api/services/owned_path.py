from __future__ import annotations
import subprocess
import pathlib
from pydantic import BaseModel

from selfprivacy_api.utils.block_devices import BlockDevice, BlockDevices


class BindError(Exception):
    pass


# May be deprecated because of Binds
class OwnedPath(BaseModel):
    path: str
    owner: str
    group: str


class Bind:
    """
    A directory that resides on some volume but we mount it into fs
    where we need it.
    Used for service data.
    """

    def __init__(self, binding_path: str, owner: str, group: str, drive: BlockDevice):
        self.binding_path = binding_path
        self.owner = owner
        self.group = group
        self.drive = drive

    # TODO: make Service return a list of binds instead of owned paths
    @staticmethod
    def from_owned_path(path: OwnedPath, drive_name: str) -> Bind:
        drive = BlockDevices().get_block_device(drive_name)
        if drive is None:
            raise BindError(f"No such drive: {drive_name}")

        return Bind(
            binding_path=path.path, owner=path.owner, group=path.group, drive=drive
        )

    def bind_foldername(self) -> str:
        return self.binding_path.split("/")[-1]

    def location_at_volume(self) -> str:
        return f"/volumes/{self.drive.name}/{self.bind_foldername()}"

    def validate(self) -> str:
        path = pathlib.Path(self.location_at_volume())

        if not path.exists():
            raise BindError(f"directory {path} is not found.")
        if not path.is_dir():
            raise BindError(f"{path} is not a directory.")
        if path.owner() != self.owner:
            raise BindError(f"{path} is not owned by {self.owner}.")

    def bind(self) -> None:
        try:
            subprocess.run(
                [
                    "mount",
                    "--bind",
                    self.location_at_volume(),
                    self.binding_path,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.output)
            raise BindError(f"Unable to mount new volume:{error.output}")

    def unbind(self) -> None:
        try:
            subprocess.run(
                ["umount", self.binding_path],
                check=True,
            )
        except subprocess.CalledProcessError:
            raise BindError(f"Unable to unmount folder {self.binding_path}.")
        pass

    def ensure_ownership(self) -> None:
        true_location = self.location_at_volume()
        try:
            subprocess.run(
                [
                    "chown",
                    "-R",
                    f"{self.owner}:{self.group}",
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
            raise BindError(error_message)
