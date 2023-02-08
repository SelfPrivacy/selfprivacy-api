import subprocess

from selfprivacy_api.backup import AbstractBackuper


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
        return f"rclone::{self.type}:{repository_name}/sfbackup"

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

    def restic_command(self, repo_name: str, *args):
        command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(repo_name),
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
        subprocess.Popen(
            backup_command,
            shell=False,
            stderr=subprocess.STDOUT,
        )

        # TODO: we might want to provide logging facilities
        # that are reroutable for testing
        # with open("/var/backup.log", "w", encoding="utf-8") as log_file:
        #     subprocess.Popen(
        #         backup_command,
        #         shell=False,
        #         stdout=log_file,
        #         stderr=subprocess.STDOUT,
        #     )
