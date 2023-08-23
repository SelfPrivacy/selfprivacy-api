from __future__ import annotations

import subprocess
import json
import datetime
import tempfile

from typing import List, TypeVar, Callable
from collections.abc import Iterable
from json.decoder import JSONDecodeError
from os.path import exists, join
from os import mkdir
from shutil import rmtree

from selfprivacy_api.backup.util import output_yielder, sync
from selfprivacy_api.backup.backuppers import AbstractBackupper
from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.backup.jobs import get_backup_job
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.jobs import Jobs, JobStatus

from selfprivacy_api.backup.local_secret import LocalBackupSecret

SHORT_ID_LEN = 8

T = TypeVar("T", bound=Callable)


def unlocked_repo(func: T) -> T:
    """unlock repo and retry if it appears to be locked"""

    def inner(self: ResticBackupper, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as error:
            if "unable to create lock" in str(error):
                self.unlock()
                return func(self, *args, **kwargs)
            else:
                raise error

    # Above, we manually guarantee that the type returned is compatible.
    return inner  # type: ignore


class ResticBackupper(AbstractBackupper):
    def __init__(self, login_flag: str, key_flag: str, storage_type: str) -> None:
        self.login_flag = login_flag
        self.key_flag = key_flag
        self.storage_type = storage_type
        self.account = ""
        self.key = ""
        self.repo = ""
        super().__init__()

    def set_creds(self, account: str, key: str, repo: str) -> None:
        self.account = account
        self.key = key
        self.repo = repo

    def restic_repo(self) -> str:
        # https://restic.readthedocs.io/en/latest/030_preparing_a_new_repo.html#other-services-via-rclone
        # https://forum.rclone.org/t/can-rclone-be-run-solely-with-command-line-options-no-config-no-env-vars/6314/5
        return f"rclone:{self.rclone_repo()}"

    def rclone_repo(self) -> str:
        return f"{self.storage_type}{self.repo}"

    def rclone_args(self):
        return "rclone.args=serve restic --stdio " + " ".join(
            self.backend_rclone_args()
        )

    def backend_rclone_args(self) -> list[str]:
        args = []
        if self.account != "":
            acc_args = [self.login_flag, self.account]
            args.extend(acc_args)
        if self.key != "":
            key_args = [self.key_flag, self.key]
            args.extend(key_args)
        return args

    def _password_command(self):
        return f"echo {LocalBackupSecret.get()}"

    def restic_command(self, *args, tag: str = "") -> List[str]:
        command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "--password-command",
            self._password_command(),
        ]
        if tag != "":
            command.extend(
                [
                    "--tag",
                    tag,
                ]
            )
        if args:
            command.extend(ResticBackupper.__flatten_list(args))
        return command

    def erase_repo(self) -> None:
        """Fully erases repo on remote, can be reinitted again"""
        command = [
            "rclone",
            "purge",
            self.rclone_repo(),
        ]
        backend_args = self.backend_rclone_args()
        if backend_args:
            command.extend(backend_args)

        with subprocess.Popen(command, stdout=subprocess.PIPE, shell=False) as handle:
            output = handle.communicate()[0].decode("utf-8")
            if handle.returncode != 0:
                raise ValueError(
                    "purge exited with errorcode",
                    handle.returncode,
                    ":",
                    output,
                )

    @staticmethod
    def __flatten_list(list_to_flatten):
        """string-aware list flattener"""
        result = []
        for item in list_to_flatten:
            if isinstance(item, Iterable) and not isinstance(item, str):
                result.extend(ResticBackupper.__flatten_list(item))
                continue
            result.append(item)
        return result

    @unlocked_repo
    def start_backup(self, folders: List[str], tag: str) -> Snapshot:
        """
        Start backup with restic
        """

        # but maybe it is ok to accept a union
        # of a string and an array of strings
        assert not isinstance(folders, str)

        backup_command = self.restic_command(
            "backup",
            "--json",
            folders,
            tag=tag,
        )

        messages = []

        service = get_service_by_id(tag)
        if service is None:
            raise ValueError("No service with id ", tag)

        job = get_backup_job(service)
        output = []
        try:
            for raw_message in output_yielder(backup_command):
                output.append(raw_message)
                message = self.parse_message(
                    raw_message,
                    job,
                )
                messages.append(message)
            return ResticBackupper._snapshot_from_backup_messages(
                messages,
                tag,
            )
        except ValueError as error:
            raise ValueError(
                "Could not create a snapshot: ",
                str(error),
                output,
                "parsed messages:",
                messages,
            ) from error

    @staticmethod
    def _snapshot_from_backup_messages(messages, repo_name) -> Snapshot:
        for message in messages:
            if message["message_type"] == "summary":
                return ResticBackupper._snapshot_from_fresh_summary(
                    message,
                    repo_name,
                )
        raise ValueError("no summary message in restic json output")

    def parse_message(self, raw_message_line: str, job=None) -> dict:
        message = ResticBackupper.parse_json_output(raw_message_line)
        if not isinstance(message, dict):
            raise ValueError("we have too many messages on one line?")
        if message["message_type"] == "status":
            if job is not None:  # only update status if we run under some job
                Jobs.update(
                    job,
                    JobStatus.RUNNING,
                    progress=int(message["percent_done"] * 100),
                )
        return message

    @staticmethod
    def _snapshot_from_fresh_summary(message: dict, repo_name) -> Snapshot:
        return Snapshot(
            # There is a discrepancy between versions of restic/rclone
            # Some report short_id in this field and some full
            id=message["snapshot_id"][0:SHORT_ID_LEN],
            created_at=datetime.datetime.now(datetime.timezone.utc),
            service_name=repo_name,
        )

    def init(self) -> None:
        init_command = self.restic_command(
            "init",
        )
        with subprocess.Popen(
            init_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as process_handle:
            output = process_handle.communicate()[0].decode("utf-8")
            if "created restic repository" not in output:
                raise ValueError("cannot init a repo: " + output)

    @unlocked_repo
    def is_initted(self) -> bool:
        command = self.restic_command(
            "check",
        )

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            shell=False,
            stderr=subprocess.STDOUT,
        ) as handle:
            output = handle.communicate()[0].decode("utf-8")
            if handle.returncode != 0:
                if "unable to create lock" in output:
                    raise ValueError("Stale lock detected: ", output)
                return False
            return True

    def unlock(self) -> None:
        """Remove stale locks."""
        command = self.restic_command(
            "unlock",
        )

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            shell=False,
            stderr=subprocess.STDOUT,
        ) as handle:
            # communication forces to complete and for returncode to get defined
            output = handle.communicate()[0].decode("utf-8")
            if handle.returncode != 0:
                raise ValueError("cannot unlock the backup repository: ", output)

    def lock(self) -> None:
        """
        Introduce a stale lock.
        Mainly for testing purposes.
        Double lock is supposed to fail
        """
        command = self.restic_command(
            "check",
        )

        # using temporary cache in /run/user/1000/restic-check-cache-817079729
        # repository 9639c714 opened (repository version 2) successfully, password is correct
        # created new cache in /run/user/1000/restic-check-cache-817079729
        # create exclusive lock for repository
        # load indexes
        # check all packs
        # check snapshots, trees and blobs
        # [0:00] 100.00%  1 / 1 snapshots
        # no errors were found

        try:
            for line in output_yielder(command):
                if "indexes" in line:
                    break
                if "unable" in line:
                    raise ValueError(line)
        except Exception as error:
            raise ValueError("could not lock repository") from error

    @unlocked_repo
    def restored_size(self, snapshot_id: str) -> int:
        """
        Size of a snapshot
        """
        command = self.restic_command(
            "stats",
            snapshot_id,
            "--json",
        )

        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        ) as handle:
            output = handle.communicate()[0].decode("utf-8")
            try:
                parsed_output = ResticBackupper.parse_json_output(output)
                return parsed_output["total_size"]
            except ValueError as error:
                raise ValueError("cannot restore a snapshot: " + output) from error

    @unlocked_repo
    def restore_from_backup(
        self,
        snapshot_id,
        folders: List[str],
        verify=True,
    ) -> None:
        """
        Restore from backup with restic
        """
        if folders is None or folders == []:
            raise ValueError("cannot restore without knowing where to!")

        with tempfile.TemporaryDirectory() as temp_dir:
            if verify:
                self._raw_verified_restore(snapshot_id, target=temp_dir)
                snapshot_root = temp_dir
                for folder in folders:
                    src = join(snapshot_root, folder.strip("/"))
                    if not exists(src):
                        raise ValueError(
                            f"No such path: {src}. We tried to find {folder}"
                        )
                    dst = folder
                    sync(src, dst)

            else:  # attempting inplace restore
                for folder in folders:
                    rmtree(folder)
                    mkdir(folder)
                self._raw_verified_restore(snapshot_id, target="/")
                return

    def _raw_verified_restore(self, snapshot_id, target="/"):
        """barebones restic restore"""
        restore_command = self.restic_command(
            "restore", snapshot_id, "--target", target, "--verify"
        )

        with subprocess.Popen(
            restore_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
        ) as handle:

            # for some reason restore does not support
            # nice reporting of progress via json
            output = handle.communicate()[0].decode("utf-8")
            if "restoring" not in output:
                raise ValueError("cannot restore a snapshot: " + output)

            assert (
                handle.returncode is not None
            )  # none should be impossible after communicate
            if handle.returncode != 0:
                raise ValueError(
                    "restore exited with errorcode",
                    handle.returncode,
                    ":",
                    output,
                )

    @unlocked_repo
    def forget_snapshot(self, snapshot_id) -> None:
        """
        Either removes snapshot or marks it for deletion later,
        depending on server settings
        """
        forget_command = self.restic_command(
            "forget",
            snapshot_id,
        )

        with subprocess.Popen(
            forget_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        ) as handle:
            # for some reason restore does not support
            # nice reporting of progress via json
            output, err = [
                string.decode(
                    "utf-8",
                )
                for string in handle.communicate()
            ]

            if "no matching ID found" in err:
                raise ValueError(
                    "trying to delete, but no such snapshot: ", snapshot_id
                )

            assert (
                handle.returncode is not None
            )  # none should be impossible after communicate
            if handle.returncode != 0:
                raise ValueError(
                    "forget exited with errorcode", handle.returncode, ":", output, err
                )

    def _load_snapshots(self) -> object:
        """
        Load list of snapshots from repository
        raises Value Error if repo does not exist
        """
        listing_command = self.restic_command(
            "snapshots",
            "--json",
        )

        with subprocess.Popen(
            listing_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as backup_listing_process_descriptor:
            output = backup_listing_process_descriptor.communicate()[0].decode("utf-8")

        if "Is there a repository at the following location?" in output:
            raise ValueError("No repository! : " + output)
        try:
            return ResticBackupper.parse_json_output(output)
        except ValueError as error:
            raise ValueError("Cannot load snapshots: ", output) from error

    @unlocked_repo
    def get_snapshots(self) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        snapshots = []
        for restic_snapshot in self._load_snapshots():
            snapshot = Snapshot(
                id=restic_snapshot["short_id"],
                created_at=restic_snapshot["time"],
                service_name=restic_snapshot["tags"][0],
            )

            snapshots.append(snapshot)
        return snapshots

    @staticmethod
    def parse_json_output(output: str) -> object:
        starting_index = ResticBackupper.json_start(output)

        if starting_index == -1:
            raise ValueError("There is no json in the restic output: " + output)

        truncated_output = output[starting_index:]
        json_messages = truncated_output.splitlines()
        if len(json_messages) == 1:
            try:
                return json.loads(truncated_output)
            except JSONDecodeError as error:
                raise ValueError(
                    "There is no json in the restic output : " + output
                ) from error

        result_array = []
        for message in json_messages:
            result_array.append(json.loads(message))
        return result_array

    @staticmethod
    def json_start(output: str) -> int:
        indices = [
            output.find("["),
            output.find("{"),
        ]
        indices = [x for x in indices if x != -1]

        if indices == []:
            return -1
        return min(indices)

    @staticmethod
    def has_json(output: str) -> bool:
        if ResticBackupper.json_start(output) == -1:
            return False
        return True
