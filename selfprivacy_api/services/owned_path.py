from __future__ import annotations

import logging
import pathlib
import subprocess
from os.path import exists

from selfprivacy_api.exceptions.services import (
    BindDirectoryNotFoundError,
    BindOperationFailedError,
    BindOwnershipFailedError,
    BindPathNotDirectoryError,
    BindPathNotOwnedError,
    BindTargetNotFoundError,
    NoSuchDriveError,
    UnbindOperationFailedError,
    UnbindTargetNotFoundError,
)
from selfprivacy_api.models.owned_path import OwnedPath
from selfprivacy_api.utils.block_devices import BlockDevice, BlockDevices

logger = logging.getLogger(__name__)

# tests override it to a tmpdir
VOLUMES_PATH = "/volumes"


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
        drive = BlockDevices().get_block_device_by_canonical_name(drive_name)
        if drive is None:
            raise NoSuchDriveError(drive_name)

        return Bind(
            binding_path=path.path, owner=path.owner, group=path.group, drive=drive
        )

    def bind_foldername(self) -> str:
        return self.binding_path.split("/")[-1]

    def location_at_volume(self) -> str:
        return f"{VOLUMES_PATH}/{self.drive.canonical_name}/{self.bind_foldername()}"

    def validate(self) -> None:
        path = pathlib.Path(self.location_at_volume())

        if not path.exists():
            raise BindDirectoryNotFoundError(str(path))
        if not path.is_dir():
            raise BindPathNotDirectoryError(str(path))
        if path.owner() != self.owner:
            raise BindPathNotOwnedError(str(path), self.owner)

    def bind(self) -> None:
        if not exists(self.binding_path):
            raise BindTargetNotFoundError(self.binding_path)

        source = self.location_at_volume()
        target = self.binding_path

        try:
            subprocess.run(
                ["mount", "--bind", source, target],
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            details = error.stderr or str(error)
            logger.error(details)
            raise BindOperationFailedError(source, target, details) from error

    def unbind(self) -> None:
        if not exists(self.binding_path):
            raise UnbindTargetNotFoundError(self.binding_path)

        try:
            subprocess.run(
                # umount -l ?
                ["umount", self.binding_path],
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            details = error.stderr or str(error)
            raise UnbindOperationFailedError(self.binding_path, details) from error

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
                text=True,
            )
        except subprocess.CalledProcessError as error:
            details = error.stderr or str(error)
            logger.error(details)
            raise BindOwnershipFailedError(true_location, details) from error
