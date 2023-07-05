from abc import ABC, abstractmethod
from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot


class AbstractBackupper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def is_initted(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_creds(self, account: str, key: str, repo: str):
        raise NotImplementedError

    @abstractmethod
    def start_backup(self, folders: List[str], repo_name: str):
        raise NotImplementedError

    @abstractmethod
    def get_snapshots(self) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        raise NotImplementedError

    @abstractmethod
    def init(self):
        raise NotImplementedError

    @abstractmethod
    def restore_from_backup(self, snapshot_id: str, folders: List[str]):
        """Restore a target folder using a snapshot"""
        raise NotImplementedError

    @abstractmethod
    def restored_size(self, snapshot_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def forget_snapshot(self, snapshot_id):
        raise NotImplementedError
