from selfprivacy_api.backup import AbstractBackuper


class ResticBackuper(AbstractBackuper):
    def __init__(self, login_flag: str, key_flag: str, type: str):
        self.login_flag = login_flag
        self.key_flag = key_flag
        self.type = type

    def restic_repo(self, repository_name: str) -> str:
        # https://restic.readthedocs.io/en/latest/030_preparing_a_new_repo.html#other-services-via-rclone
        # https://forum.rclone.org/t/can-rclone-be-run-solely-with-command-line-options-no-config-no-env-vars/6314/5
        return f"rclone::{self.type}:{self._repository_name}/sfbackup"

    def rclone_args(self):
        return "rclone.args=serve restic --stdio" + self.backend_rclone_args()

    def backend_rclone_args(self, account: str, key: str):
        return f"{self.login_flag} {account} {self.key_flag} {key}"

    def restic_command(self, account: str, key: str, *args):
        return [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(account, key),
        ].extend(args)
