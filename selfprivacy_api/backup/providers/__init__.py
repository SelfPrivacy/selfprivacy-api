from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.backup.providers.provider import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.backup.providers.memory import InMemoryBackup
from selfprivacy_api.backup.providers.local_file import LocalFileBackup

PROVIDER_MAPPING = {
    BackupProvider.BACKBLAZE: Backblaze,
    BackupProvider.MEMORY: InMemoryBackup,
    BackupProvider.FILE: LocalFileBackup,
}


def get_provider(provider_type: BackupProvider) -> AbstractBackupProvider:
    return PROVIDER_MAPPING[provider_type]
