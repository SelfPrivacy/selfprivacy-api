import pytest
import os.path as path
from os import makedirs
from os import remove
from os import listdir

from selfprivacy_api.services.test_service import DummyService

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.backup import Backups
import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider

from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.graphql.queries.providers import BackupProvider


TESTFILE_BODY = "testytest!"
REPO_NAME = "test_backup"


@pytest.fixture(scope="function")
def backups(tmpdir):
    test_repo_path = path.join(tmpdir, "totallyunrelated")
    backups = Backups(test_repo_path)
    backups.reset()
    return backups


@pytest.fixture()
def backups_backblaze(generic_userdata):
    backups = Backups()
    backups.reset()
    return backups


@pytest.fixture()
def raw_dummy_service(tmpdir, backups):
    service_dir = path.join(tmpdir, "test_service")
    makedirs(service_dir)

    testfile_path = path.join(service_dir, "testfile.txt")
    with open(testfile_path, "w") as file:
        file.write(TESTFILE_BODY)

    # we need this to not change get_location() much
    class TestDummyService(DummyService, location=service_dir):
        pass

    service = TestDummyService()
    return service


@pytest.fixture()
def dummy_service(tmpdir, backups, raw_dummy_service):
    service = raw_dummy_service
    repo_path = path.join(tmpdir, "test_repo")
    assert not path.exists(repo_path)
    # assert not repo_path

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


def test_config_load(generic_userdata):
    backups = Backups()
    backups.reset()
    provider = backups.provider

    assert provider is not None
    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_file_backend_init(file_backup):
    file_backup.backuper.init("somerepo")


def test_backup_simple_file(raw_dummy_service, file_backup):
    # temporarily incomplete
    service = raw_dummy_service
    assert service is not None
    assert file_backup is not None

    name = service.get_id()
    file_backup.backuper.init(name)


def test_backup_service(dummy_service, backups):
    backups.back_up(dummy_service)


def test_no_repo(memory_backup):
    with pytest.raises(ValueError):
        assert memory_backup.backuper.get_snapshots("") == []


def test_one_snapshot(backups, dummy_service):
    backups.back_up(dummy_service)

    snaps = backups.get_snapshots(dummy_service)
    assert len(snaps) == 1
    snap = snaps[0]
    assert snap.service_name == dummy_service.get_id()


def test_restore(backups, dummy_service):
    service_folder = dummy_service.get_location()
    file_to_nuke = listdir(service_folder)[0]
    assert file_to_nuke is not None
    path_to_nuke = path.join(service_folder, file_to_nuke)

    backups.back_up(dummy_service)
    snap = backups.get_snapshots(dummy_service)[0]
    assert snap is not None

    assert path.exists(path_to_nuke)
    remove(path_to_nuke)
    assert not path.exists(path_to_nuke)

    backups.restore_service_from_snapshot(dummy_service, snap.id)
    assert path.exists(path_to_nuke)


def test_sizing(backups, dummy_service):
    backups.back_up(dummy_service)
    snap = backups.get_snapshots(dummy_service)[0]
    size = backups.service_snapshot_size(dummy_service, snap.id)
    assert size is not None
    assert size > 0


def test_redis_storage(backups_backblaze):
    backups = Backups()
    backups.reset()
    provider = backups.provider

    assert provider is not None

    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"

    backups.store_provider_redis(provider)
    restored_provider = backups.load_provider_redis()
    assert isinstance(restored_provider, Backblaze)
    assert restored_provider.login == "ID"
    assert restored_provider.key == "KEY"
