from abc import ABC, abstractmethod
from typing import List

from selfprivacy_api.models.backup.snapshot import Snapshot
from selfprivacy_api.graphql.common_types.backup import BackupReason


class AbstractBackupper(ABC):
    """Abstract class for backuppers"""

    # flake8: noqa: B027
    def __init__(self) -> None:
        pass

    @abstractmethod
    def is_initted(self) -> bool:
        """Returns true if the repository is initted"""
        raise NotImplementedError

    @abstractmethod
    def set_creds(self, account: str, key: str, repo: str) -> None:
        """Set the credentials for the backupper"""
        raise NotImplementedError

    @abstractmethod
    async def start_backup(
        self,
        folders: List[str],
        service_name: str,
        reason: BackupReason = BackupReason.EXPLICIT,
    ) -> Snapshot:
        """Start a backup of the given folders"""
        raise NotImplementedError

    @abstractmethod
    def get_snapshots(self) -> List[Snapshot]:
        """Get all snapshots from the repo"""
        raise NotImplementedError

    @abstractmethod
    def init(self) -> None:
        """Initialize the repository"""
        raise NotImplementedError

    @abstractmethod
    def erase_repo(self) -> None:
        """Completely empties the remote"""
        raise NotImplementedError

    @abstractmethod
    def restore_from_backup(
        self,
        snapshot_id: str,
        folders: List[str],
        verify=True,
    ) -> None:
        """Restore a target folder using a snapshot"""
        raise NotImplementedError

    @abstractmethod
    def restored_size(self, snapshot_id: str) -> int:
        """Get the size of the restored snapshot"""
        raise NotImplementedError

    @abstractmethod
    def forget_snapshot(self, snapshot_id) -> None:
        """Forget a snapshot"""
        raise NotImplementedError

    @abstractmethod
    def forget_snapshots(self, snapshot_ids: List[str]) -> None:
        """Maybe optimized deletion of a batch of snapshots, just cycling if unsupported"""
        raise NotImplementedError
