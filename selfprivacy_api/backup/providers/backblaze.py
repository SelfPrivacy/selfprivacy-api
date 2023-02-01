from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class Backblaze(AbstractBackupProvider):
    backuper = ResticBackuper("--b2-account", "--b2-key", "b2")
