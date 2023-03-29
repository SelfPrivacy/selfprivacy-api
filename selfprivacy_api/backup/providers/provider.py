"""
An abstract class for BackBlaze, S3 etc.
It assumes that while some providers are supported via restic/rclone, others may
require different backends
"""
from abc import ABC
from selfprivacy_api.backup.backuper import AbstractBackuper


class AbstractBackupProvider(ABC):
    @property
    def backuper(self) -> AbstractBackuper:
        raise NotImplementedError

    def __init__(self, login="", key=""):
        self.login = login
        self.key = key
