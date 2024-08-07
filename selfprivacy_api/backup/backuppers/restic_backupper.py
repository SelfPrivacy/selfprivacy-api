from __future__ import annotations

import subprocess
import json
import datetime
import tempfile

from typing import List, Optional, TypeVar, Callable
from collections.abc import Iterable
from json.decoder import JSONDecodeError
from os.path import exists, join
from os import mkdir
from shutil import rmtree

from selfprivacy_api.graphql.common_types.backup import BackupReason
from selfprivacy_api.backup.util import output_yielder, sync
from selfprivacy_api.backup.backuppers import AbstractBackupper
from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.backup.jobs import get_backup_job
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.jobs import Jobs, JobStatus, Job

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

    def restic_command(self, *args, tags: Optional[List[str]] = None) -> List[str]:
        """
        Construct a restic command against the currently configured repo
        Can support [nested] arrays as arguments, will flatten them into the final commmand
        """
        if tags is None:
            tags = []

        command = [
            "restic",
            "--verbose",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "--password-command",
            self._password_command(),
        ]
        if tags != []:
            for tag in tags:
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

    @staticmethod
    def _run_backup_command(
        backup_command: List[str], job: Optional[Job]
    ) -> List[dict]:
        """And handle backup output"""
        messages = []
        output = []
        restic_reported_error = False

        for raw_message in output_yielder(backup_command):
            if "ERROR:" in raw_message:
                restic_reported_error = True
            output.append(raw_message)

            if not restic_reported_error:
                message = ResticBackupper.parse_message(raw_message, job)
                messages.append(message)

        if restic_reported_error:
            raise ValueError(
                "Restic returned error(s): ",
                output,
            )

        return messages

    @staticmethod
    def _replace_in_array(array: List[str], target, replacement) -> None:
        if target == "":
            return

        for i, value in enumerate(array):
            if target in value:
                array[i] = array[i].replace(target, replacement)

    def _censor_command(self, command: List[str]) -> List[str]:
        result = command.copy()
        ResticBackupper._replace_in_array(result, self.key, "CENSORED")
        ResticBackupper._replace_in_array(result, LocalBackupSecret.get(), "CENSORED")
        return result

    @staticmethod
    def _get_backup_job(service_name: str) -> Optional[Job]:
        service = get_service_by_id(service_name)
        if service is None:
            raise ValueError("No service with id ", service_name)

        return get_backup_job(service)

    @unlocked_repo
    def start_backup(
        self,
        folders: List[str],
        service_name: str,
        reason: BackupReason = BackupReason.EXPLICIT,
    ) -> Snapshot:
        """
        Start backup with restic
        """
        assert len(folders) != 0

        job = ResticBackupper._get_backup_job(service_name)

        tags = [service_name, reason.value]
        backup_command = self.restic_command(
            "backup",
            "--json",
            folders,
            tags=tags,
        )

        try:
            messages = ResticBackupper._run_backup_command(backup_command, job)

            id = ResticBackupper._snapshot_id_from_backup_messages(messages)
            return Snapshot(
                created_at=datetime.datetime.now(datetime.timezone.utc),
                id=id,
                service_name=service_name,
                reason=reason,
            )

        except ValueError as error:
            raise ValueError(
                "Could not create a snapshot: ",
                str(error),
                "command: ",
                self._censor_command(backup_command),
            ) from error

    @staticmethod
    def _snapshot_id_from_backup_messages(messages) -> str:
        for message in messages:
            if message["message_type"] == "summary":
                # There is a discrepancy between versions of restic/rclone
                # Some report short_id in this field and some full
                return message["snapshot_id"][0:SHORT_ID_LEN]

        raise ValueError("no summary message in restic json output")

    @staticmethod
    def parse_message(raw_message_line: str, job: Optional[Job] = None) -> dict:
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

    def forget_snapshot(self, snapshot_id: str) -> None:
        self.forget_snapshots([snapshot_id])

    @unlocked_repo
    def forget_snapshots(self, snapshot_ids: List[str]) -> None:
        # in case the backupper program supports batching, otherwise implement it by cycling
        forget_command = self.restic_command(
            "forget",
            [snapshot_ids],
            # TODO: prune should be done in a separate process
            "--prune",
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
                    "trying to delete, but no such snapshot(s): ", snapshot_ids
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
            # Compatibility with previous snaps:
            if len(restic_snapshot["tags"]) == 1:
                reason = BackupReason.EXPLICIT
            else:
                reason = restic_snapshot["tags"][1]

            snapshot = Snapshot(
                id=restic_snapshot["short_id"],
                created_at=restic_snapshot["time"],
                service_name=restic_snapshot["tags"][0],
                reason=reason,
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
