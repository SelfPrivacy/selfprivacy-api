import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.graphql.queries.providers import BackupProvider


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze
