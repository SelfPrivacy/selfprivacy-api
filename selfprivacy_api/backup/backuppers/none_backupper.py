from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.backup.backuppers import AbstractBackupper
from selfprivacy_api.graphql.common_types.backup import BackupReason


class NoneBackupper(AbstractBackupper):
    """A backupper that does nothing"""

    def is_initted(self, repo_name: str = "") -> bool:
        return False

    def set_creds(self, account: str, key: str, repo: str):
        pass

    def start_backup(
        self, folders: List[str], tag: str, reason: BackupReason = BackupReason.EXPLICIT
    ):
        raise NotImplementedError

    def get_snapshots(self) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        return []

    def init(self):
        raise NotImplementedError

    def erase_repo(self) -> None:
        """Completely empties the remote"""
        # this one is already empty
        pass

    def restore_from_backup(self, snapshot_id: str, folders: List[str], verify=True):
        """Restore a target folder using a snapshot"""
        raise NotImplementedError

    def restored_size(self, snapshot_id: str) -> int:
        raise NotImplementedError

    def forget_snapshot(self, snapshot_id):
        raise NotImplementedError("forget_snapshot")

    def forget_snapshots(self, snapshots):
        raise NotImplementedError("forget_snapshots")
