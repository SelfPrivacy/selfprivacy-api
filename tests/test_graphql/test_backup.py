import pytest

from selfprivacy_api.services.test_service import DummyService

import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.graphql.queries.providers import BackupProvider


@pytest.fixture()
def test_service(tmpdir):
    return DummyService(tmpdir)


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_backup(test_service):
    # temporarily incomplete
    assert test_service is not None
