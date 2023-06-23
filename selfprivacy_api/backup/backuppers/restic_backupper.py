import subprocess
import json
import datetime

from typing import List
from collections.abc import Iterable
from json.decoder import JSONDecodeError

from selfprivacy_api.backup.backuppers import AbstractBackupper
from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.backup.jobs import get_backup_job
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.jobs import Jobs, JobStatus

from selfprivacy_api.backup.local_secret import LocalBackupSecret


class ResticBackupper(AbstractBackupper):
    def __init__(self, login_flag: str, key_flag: str, type: str):
        self.login_flag = login_flag
        self.key_flag = key_flag
        self.type = type
        self.account = ""
        self.key = ""
        self.repo = ""

    def set_creds(self, account: str, key: str, repo: str):
        self.account = account
        self.key = key
        self.repo = repo

    def restic_repo(self) -> str:
        # https://restic.readthedocs.io/en/latest/030_preparing_a_new_repo.html#other-services-via-rclone
        # https://forum.rclone.org/t/can-rclone-be-run-solely-with-command-line-options-no-config-no-env-vars/6314/5
        return f"rclone:{self.type}{self.repo}"

    def rclone_args(self):
        return "rclone.args=serve restic --stdio" + self.backend_rclone_args()

    def backend_rclone_args(self) -> str:
        acc_arg = ""
        key_arg = ""
        if self.account != "":
            acc_arg = f"{self.login_flag} {self.account}"
        if self.key != "":
            key_arg = f"{self.key_flag} {self.key}"

        return f"{acc_arg} {key_arg}"

    def _password_command(self):
        return f"echo {LocalBackupSecret.get()}"

    def restic_command(self, *args, tag: str = ""):
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
        if args != []:
            command.extend(ResticBackupper.__flatten_list(args))
        return command

    @staticmethod
    def __flatten_list(list):
        """string-aware list flattener"""
        result = []
        for item in list:
            if isinstance(item, Iterable) and not isinstance(item, str):
                result.extend(ResticBackupper.__flatten_list(item))
                continue
            result.append(item)
        return result

    @staticmethod
    def output_yielder(command):
        with subprocess.Popen(
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ) as handle:
            for line in iter(handle.stdout.readline, ""):
                if "NOTICE:" not in line:
                    yield line

    def start_backup(self, folders: List[str], tag: str):
        """
        Start backup with restic
        """

        # but maybe it is ok to accept a union of a string and an array of strings
        assert not isinstance(folders, str)

        backup_command = self.restic_command(
            "backup",
            "--json",
            folders,
            tag=tag,
        )

        messages = []
        job = get_backup_job(get_service_by_id(tag))
        try:
            for raw_message in ResticBackupper.output_yielder(backup_command):
                message = self.parse_message(raw_message, job)
                messages.append(message)
            return ResticBackupper._snapshot_from_backup_messages(messages, tag)
        except ValueError as e:
            raise ValueError("could not create a snapshot: ", messages) from e

    @staticmethod
    def _snapshot_from_backup_messages(messages, repo_name) -> Snapshot:
        for message in messages:
            if message["message_type"] == "summary":
                return ResticBackupper._snapshot_from_fresh_summary(message, repo_name)
        raise ValueError("no summary message in restic json output")

    def parse_message(self, raw_message, job=None) -> object:
        message = ResticBackupper.parse_json_output(raw_message)
        if message["message_type"] == "status":
            if job is not None:  # only update status if we run under some job
                Jobs.update(
                    job,
                    JobStatus.RUNNING,
                    progress=int(message["percent_done"]),
                )
        return message

    @staticmethod
    def _snapshot_from_fresh_summary(message: object, repo_name) -> Snapshot:
        return Snapshot(
            id=message["snapshot_id"],
            created_at=datetime.datetime.now(datetime.timezone.utc),
            service_name=repo_name,
        )

    def init(self):
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
            if not "created restic repository" in output:
                raise ValueError("cannot init a repo: " + output)

    def is_initted(self) -> bool:
        command = self.restic_command(
            "check",
            "--json",
        )

        with subprocess.Popen(command, stdout=subprocess.PIPE, shell=False) as handle:
            output = handle.communicate()[0].decode("utf-8")
            if not ResticBackupper.has_json(output):
                return False
            # raise NotImplementedError("error(big): " + output)
            return True

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
            shell=False,
        ) as handle:
            output = handle.communicate()[0].decode("utf-8")
            try:
                parsed_output = ResticBackupper.parse_json_output(output)
                return parsed_output["total_size"]
            except ValueError as e:
                raise ValueError("cannot restore a snapshot: " + output) from e

    def restore_from_backup(self, snapshot_id, folders):
        """
        Restore from backup with restic
        """
        # snapshots save the path of the folder in the file system
        # I do not alter the signature yet because maybe this can be
        # changed with flags
        restore_command = self.restic_command(
            "restore",
            snapshot_id,
            "--target",
            "/",
        )

        with subprocess.Popen(
            restore_command, stdout=subprocess.PIPE, shell=False
        ) as handle:

            # for some reason restore does not support nice reporting of progress via json
            output = handle.communicate()[0].decode("utf-8")
            if "restoring" not in output:
                raise ValueError("cannot restore a snapshot: " + output)

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
        except ValueError as e:
            raise ValueError("Cannot load snapshots: ") from e

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
            raise ValueError("There is no json in the restic output : " + output)

        truncated_output = output[starting_index:]
        json_messages = truncated_output.splitlines()
        if len(json_messages) == 1:
            try:
                return json.loads(truncated_output)
            except JSONDecodeError as e:
                raise ValueError(
                    "There is no json in the restic output : " + output
                ) from e

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
