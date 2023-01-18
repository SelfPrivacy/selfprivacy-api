"""Restic singleton controller."""
from datetime import datetime
import json
import subprocess
import os
from enum import Enum
import portalocker
from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass


class ResticStates(Enum):
    """Restic states enum."""

    NO_KEY = 0
    NOT_INITIALIZED = 1
    INITIALIZED = 2
    BACKING_UP = 3
    RESTORING = 4
    ERROR = 5
    INITIALIZING = 6


class ResticController(metaclass=SingletonMetaclass):
    """
    States in wich the restic_controller may be
    - no backblaze key
    - backblaze key is provided, but repository is not initialized
    - backblaze key is provided, repository is initialized
    - fetching list of snapshots
    - creating snapshot, current progress can be retrieved
    - recovering from snapshot

    Any ongoing operation acquires the lock
    Current state can be fetched with get_state()
    """

    _initialized = False

    def __init__(self):
        if self._initialized:
            return
        self.state = ResticStates.NO_KEY
        self.lock = False
        self.progress = 0
        self._backblaze_account = None
        self._backblaze_key = None
        self._repository_name = None
        self.snapshot_list = []
        self.error_message = None
        self._initialized = True
        self.load_configuration()
        self.write_rclone_config()
        self.load_snapshots()

    def load_configuration(self):
        """Load current configuration from user data to singleton."""
        with ReadUserData() as user_data:
            self._backblaze_account = user_data["backblaze"]["accountId"]
            self._backblaze_key = user_data["backblaze"]["accountKey"]
            self._repository_name = user_data["backblaze"]["bucket"]
        if self._backblaze_account and self._backblaze_key and self._repository_name:
            self.state = ResticStates.INITIALIZING
        else:
            self.state = ResticStates.NO_KEY

    def write_rclone_config(self):
        """
        Open /root/.config/rclone/rclone.conf with portalocker
        and write configuration in the following format:
            [backblaze]
            type = b2
            account = {self.backblaze_account}
            key = {self.backblaze_key}
        """
        with portalocker.Lock(
            "/root/.config/rclone/rclone.conf", "w", timeout=None
        ) as rclone_config:
            rclone_config.write(
                f"[backblaze]\n"
                f"type = b2\n"
                f"account = {self._backblaze_account}\n"
                f"key = {self._backblaze_key}\n"
            )

    def load_snapshots(self):
        """
        Load list of snapshots from repository
        """
        backup_listing_command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "snapshots",
            "--json",
        ]

        if self.state in (ResticStates.BACKING_UP, ResticStates.RESTORING):
            return
        with subprocess.Popen(
            backup_listing_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as backup_listing_process_descriptor:
            snapshots_list = backup_listing_process_descriptor.communicate()[0].decode(
                "utf-8"
            )
        try:
            starting_index = snapshots_list.find("[")
            json.loads(snapshots_list[starting_index:])
            self.snapshot_list = json.loads(snapshots_list[starting_index:])
            self.state = ResticStates.INITIALIZED
            print(snapshots_list)
        except ValueError:
            if "Is there a repository at the following location?" in snapshots_list:
                self.state = ResticStates.NOT_INITIALIZED
                return
            self.state = ResticStates.ERROR
            self.error_message = snapshots_list
            return

    def restic_repo(self):
        return f"rclone:backblaze:{self._repository_name}/sfbackup"

    def rclone_args(self):
        return "rclone.args=serve restic --stdio"

    def initialize_repository(self):
        """
        Initialize repository with restic
        """
        initialize_repository_command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "init",
        ]
        with subprocess.Popen(
            initialize_repository_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as initialize_repository_process_descriptor:
            msg = initialize_repository_process_descriptor.communicate()[0].decode(
                "utf-8"
            )
            if initialize_repository_process_descriptor.returncode == 0:
                self.state = ResticStates.INITIALIZED
            else:
                self.state = ResticStates.ERROR
                self.error_message = msg

        self.state = ResticStates.INITIALIZED

    def start_backup(self):
        """
        Start backup with restic
        """
        backup_command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "--verbose",
            "--json",
            "backup",
            "/var",
        ]
        with open("/var/backup.log", "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                backup_command,
                shell=False,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        self.state = ResticStates.BACKING_UP
        self.progress = 0

    def check_progress(self):
        """
        Check progress of ongoing backup operation
        """
        backup_status_check_command = ["tail", "-1", "/var/backup.log"]

        if self.state in (ResticStates.NO_KEY, ResticStates.NOT_INITIALIZED):
            return

        # If the log file does not exists
        if os.path.exists("/var/backup.log") is False:
            self.state = ResticStates.INITIALIZED

        with subprocess.Popen(
            backup_status_check_command,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as backup_status_check_process_descriptor:
            backup_process_status = (
                backup_status_check_process_descriptor.communicate()[0].decode("utf-8")
            )

        try:
            status = json.loads(backup_process_status)
        except ValueError:
            print(backup_process_status)
            self.error_message = backup_process_status
            return
        if status["message_type"] == "status":
            self.progress = status["percent_done"]
            self.state = ResticStates.BACKING_UP
        elif status["message_type"] == "summary":
            self.state = ResticStates.INITIALIZED
            self.progress = 0
            self.snapshot_list.append(
                {
                    "short_id": status["snapshot_id"],
                    # Current time in format 2021-12-02T00:02:51.086452543+03:00
                    "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
                }
            )

    def restore_from_backup(self, snapshot_id):
        """
        Restore from backup with restic
        """
        backup_restoration_command = [
            "restic",
            "-o",
            self.rclone_args(),
            "-r",
            self.restic_repo(),
            "restore",
            snapshot_id,
            "--target",
            "/",
        ]

        self.state = ResticStates.RESTORING

        subprocess.run(backup_restoration_command, shell=False)

        self.state = ResticStates.INITIALIZED
