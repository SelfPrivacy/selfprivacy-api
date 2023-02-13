from abc import ABC, abstractmethod
from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot


class AbstractBackuper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def start_backup(self, folder: str, repo_name: str):
        raise NotImplementedError

    @abstractmethod
    def get_snapshots(self, repo_name) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        raise NotImplementedError
