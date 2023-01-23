from .provider import AbstractBackupProvider
from selfprivacy_api.backup.restic_backuper import ResticBackuper


class Backblaze(AbstractBackupProvider):
    backuper = ResticBackuper()
