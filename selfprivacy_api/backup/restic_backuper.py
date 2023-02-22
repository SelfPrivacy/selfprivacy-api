import subprocess
import json

from typing import List

from selfprivacy_api.backup.backuper import AbstractBackuper
from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.backup.local_secret import LocalBackupSecret


class ResticBackuper(AbstractBackuper):
    def __init__(self, login_flag: str, key_flag: str, type: str):
        self.login_flag = login_flag
        self.key_flag = key_flag
        self.type = type
        self.account = ""
        self.key = ""

    def set_creds(self, account: str, key: str):
        self.account = account
        self.key = key

    def restic_repo(self, repository_name: str) -> str:
        # https://restic.readthedocs.io/en/latest/030_preparing_a_new_repo.html#other-services-via-rclone
        # https://forum.rclone.org/t/can-rclone-be-run-solely-with-command-line-options-no-config-no-env-vars/6314/5
        return f"rclone:{self.type}{repository_name}/sfbackup"

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

    def restic_command(self, repo_name: str, *args):
        command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(repo_name),
            "--password-command",
            self._password_command(),
        ]
        if args != []:
            command.extend(args)
        return command

    def start_backup(self, folder: str, repo_name: str):
        """
        Start backup with restic
        """
        backup_command = self.restic_command(
            repo_name,
            "backup",
            folder,
        )
        with subprocess.Popen(
            backup_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as handle:
            output = handle.communicate()[0].decode("utf-8")
            if "saved" not in output:
                raise ValueError("could not create a new snapshot: " + output)

    def init(self, repo_name):
        init_command = self.restic_command(
            repo_name,
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

    def restore_from_backup(self, repo_name, snapshot_id, folder):
        """
        Restore from backup with restic
        """
        restore_command = self.restic_command(
            repo_name, "restore", snapshot_id, "--target", folder
        )

        subprocess.run(restore_command, shell=False)

    def _load_snapshots(self, repo_name) -> object:
        """
        Load list of snapshots from repository
        raises Value Error if repo does not exist
        """
        listing_command = self.restic_command(
            repo_name,
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
            return self.parse_snapshot_output(output)
        except ValueError as e:
            raise ValueError("Cannot load snapshots: ") from e

    def get_snapshots(self, repo_name) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        snapshots = []
        for restic_snapshot in self._load_snapshots(repo_name):
            snapshot = Snapshot(
                id=restic_snapshot["short_id"],
                created_at=restic_snapshot["time"],
                service_name=repo_name,
            )

            snapshots.append(snapshot)
        return snapshots

    def parse_snapshot_output(self, output: str) -> object:
        if "[" not in output:
            raise ValueError("There is no json in the restic snapshot output")
        starting_index = output.find("[")
        return json.loads(output[starting_index:])
