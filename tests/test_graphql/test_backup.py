import pytest
import os.path as path

from selfprivacy_api.services.test_service import DummyService

from selfprivacy_api.backup import Backups
import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.graphql.queries.providers import BackupProvider


TESTFILE_BODY = "testytest!"
REPO_NAME = "test_backup"


@pytest.fixture()
def test_service(tmpdir, backups):
    testile_path = path.join(tmpdir, "testfile.txt")
    with open(testile_path, "w") as file:
        file.write(TESTFILE_BODY)

    # we need this to not change get_location() much
    class TestDummyService(DummyService, location=tmpdir):
        pass

    service = TestDummyService()
    backups.init_repo(service)
    return service


@pytest.fixture()
def memory_backup() -> AbstractBackupProvider:
    ProviderClass = providers.get_provider(BackupProvider.MEMORY)
    assert ProviderClass is not None
    memory_provider = ProviderClass(login="", key="")
    assert memory_provider is not None
    return memory_provider


@pytest.fixture()
def file_backup(tmpdir) -> AbstractBackupProvider:
    test_repo_path = path.join(tmpdir, "test_repo")
    ProviderClass = providers.get_provider(BackupProvider.FILE)
    assert ProviderClass is not None
    provider = ProviderClass(test_repo_path)
    assert provider is not None
    return provider


@pytest.fixture()
def backups():
    return Backups()


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_file_backend_init(file_backup):
    file_backup.backuper.init("somerepo")


def test_backup_simple(test_service, memory_backup):
    # temporarily incomplete
    assert test_service is not None
    assert memory_backup is not None
    memory_backup.backuper.start_backup(test_service.get_location(), REPO_NAME)


def test_backup_service(test_service, backups):
    backups.back_up(test_service)


def test_no_repo(memory_backup):
    with pytest.raises(ValueError):
        assert memory_backup.backuper.get_snapshots("") == []


# def test_one_snapshot(backups, test_service):
#     backups.back_up(test_service)
#     assert len(backups.get_snapshots(test_service)) == 1
