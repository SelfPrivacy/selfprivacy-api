from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.backup.providers.provider import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze

PROVIDER_MAPPING = {
    BackupProvider.BACKBLAZE: Backblaze
}

def get_provider(provider_type : BackupProvider) -> AbstractBackupProvider:
    return PROVIDER_MAPPING[provider_type]
