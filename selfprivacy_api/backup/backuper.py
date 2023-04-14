from abc import ABC, abstractmethod
from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot


class AbstractBackuper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def is_initted(self, repo_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start_backup(self, folders: List[str], repo_name: str):
        raise NotImplementedError

    @abstractmethod
    def get_snapshots(self, repo_name) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        raise NotImplementedError

    @abstractmethod
    def init(self, repo_name):
        raise NotImplementedError

    @abstractmethod
    def restore_from_backup(self, repo_name: str, snapshot_id: str, folders: List[str]):
        """Restore a target folder using a snapshot"""
        raise NotImplementedError

    @abstractmethod
    def restored_size(self, repo_name, snapshot_id) -> float:
        raise NotImplementedError
