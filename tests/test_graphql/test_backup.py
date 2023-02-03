import pytest
import os.path as path

from selfprivacy_api.services.test_service import DummyService

import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.graphql.queries.providers import BackupProvider


TESTFILE_BODY = "testytest!"


@pytest.fixture()
def test_service(tmpdir):
    testile_path = path.join(tmpdir, "testfile.txt")
    with open(testile_path, "w") as file:
        file.write(TESTFILE_BODY)
    return DummyService(tmpdir)


@pytest.fixture()
def memory_backup():
    ProviderClass = providers.get_provider(BackupProvider.MEMORY)
    assert ProviderClass is not None
    memory_provider = ProviderClass(login="", key="")
    assert memory_provider is not None
    return memory_provider


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_backup_service(test_service, memory_backup):
    # temporarily incomplete
    assert test_service is not None
    assert memory_backup is not None
