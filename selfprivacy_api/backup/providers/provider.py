"""
An abstract class for BackBlaze, S3 etc.
It assumes that while some providers are supported via restic/rclone, others
may require different backends
"""
from abc import ABC, abstractmethod
from selfprivacy_api.backup.backuppers import AbstractBackuper
from selfprivacy_api.graphql.queries.providers import (
    BackupProvider as BackupProviderEnum,
)


class AbstractBackupProvider(ABC):
    @property
    @abstractmethod
    def backuper(self) -> AbstractBackuper:
        raise NotImplementedError

    name: BackupProviderEnum

    def __init__(self, login="", key="", location="", repo_id=""):
        self.backuper.set_creds(login, key, location)
        self.login = login
        self.key = key
        self.location = location
        # We do not need to do anything with this one
        # Just remember in case the app forgets
        self.repo_id = repo_id
