from __future__ import annotations
import subprocess
import pathlib
from pydantic import BaseModel
from os.path import exists

from selfprivacy_api.utils.block_devices import BlockDevice, BlockDevices

# tests override it to a tmpdir
VOLUMES_PATH = "/volumes"


class BindError(Exception):
    pass


class OwnedPath(BaseModel):
    """
    A convenient interface for explicitly defining ownership of service folders.
    One overrides Service.get_owned_paths() for this.

    Why this exists?:
    One could use Bind to define ownership but then one would need to handle drive which
    is unnecessary and produces code duplication.

    It is also somewhat semantically wrong to include Owned Path into Bind
    instead of user and group. Because owner and group in Bind are applied to
    the original folder on the drive, not to the binding path. But maybe it is
    ok since they are technically both owned. Idk yet.
    """

    path: str
    owner: str
    group: str


class Bind:
    """
    A directory that resides on some volume but we mount it into fs where we need it.
    Used for storing service data.
    """

    def __init__(self, binding_path: str, owner: str, group: str, drive: BlockDevice):
        self.binding_path = binding_path
        self.owner = owner
        self.group = group
        self.drive = drive

    # TODO: delete owned path interface from Service
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
        return f"{VOLUMES_PATH}/{self.drive.name}/{self.bind_foldername()}"

    def validate(self) -> None:
        path = pathlib.Path(self.location_at_volume())

        if not path.exists():
            raise BindError(f"directory {path} is not found.")
        if not path.is_dir():
            raise BindError(f"{path} is not a directory.")
        if path.owner() != self.owner:
            raise BindError(f"{path} is not owned by {self.owner}.")

    def bind(self) -> None:
        if not exists(self.binding_path):
            raise BindError(f"cannot bind to a non-existing path: {self.binding_path}")

        source = self.location_at_volume()
        target = self.binding_path

        try:
            subprocess.run(
                ["mount", "--bind", source, target],
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(error.stderr)
            raise BindError(f"Unable to bind {source} to {target} :{error.stderr}")

    def unbind(self) -> None:
        if not exists(self.binding_path):
            raise BindError(f"cannot unbind a non-existing path: {self.binding_path}")

        try:
            subprocess.run(
                # umount -l ?
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
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as error:
            print(error.stderr)
            error_message = (
                f"Unable to set ownership of {true_location} :{error.stderr}"
            )
            raise BindError(error_message)
