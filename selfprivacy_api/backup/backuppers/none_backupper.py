from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.backup.backuppers import AbstractBackuper


class NoneBackupper(AbstractBackuper):
    def is_initted(self, repo_name: str = "") -> bool:
        return False

    def set_creds(self, account: str, key: str, repo: str):
        pass

    def start_backup(self, folders: List[str], repo_name: str):
        raise NotImplementedError

    def get_snapshots(self, repo_name) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        raise NotImplementedError

    def init(self, repo_name):
        raise NotImplementedError

    def restore_from_backup(self, repo_name: str, snapshot_id: str, folders: List[str]):
        """Restore a target folder using a snapshot"""
        raise NotImplementedError

    def restored_size(self, repo_name, snapshot_id) -> float:
        raise NotImplementedError
