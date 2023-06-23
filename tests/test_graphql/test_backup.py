import pytest
import os.path as path
from os import makedirs
from os import remove
from os import listdir
from datetime import datetime, timedelta, timezone

import selfprivacy_api.services as services
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.test_service import DummyService
from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.jobs import Jobs, JobStatus

from selfprivacy_api.backup import Backups
import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider
from selfprivacy_api.backup.providers.backblaze import Backblaze

from selfprivacy_api.backup.tasks import start_backup, restore_snapshot
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.jobs import get_backup_job


TESTFILE_BODY = "testytest!"
TESTFILE_2_BODY = "testissimo!"
REPO_NAME = "test_backup"


@pytest.fixture(scope="function")
def backups(tmpdir):
    Backups.reset()

    test_repo_path = path.join(tmpdir, "totallyunrelated")
    Backups.set_localfile_repo(test_repo_path)

    Jobs.reset()


@pytest.fixture()
def backups_backblaze(generic_userdata):
    Backups.reset(reset_json=False)


@pytest.fixture()
def raw_dummy_service(tmpdir, backups):
    dirnames = ["test_service", "also_test_service"]
    service_dirs = []
    for d in dirnames:
        service_dir = path.join(tmpdir, d)
        makedirs(service_dir)
        service_dirs.append(service_dir)

    testfile_path_1 = path.join(service_dirs[0], "testfile.txt")
    with open(testfile_path_1, "w") as file:
        file.write(TESTFILE_BODY)

    testfile_path_2 = path.join(service_dirs[1], "testfile2.txt")
    with open(testfile_path_2, "w") as file:
        file.write(TESTFILE_2_BODY)

    # we need this to not change get_folders() much
    class TestDummyService(DummyService, folders=service_dirs):
        pass

    service = TestDummyService()
    return service


@pytest.fixture()
def dummy_service(tmpdir, backups, raw_dummy_service):
    service = raw_dummy_service
    repo_path = path.join(tmpdir, "test_repo")
    assert not path.exists(repo_path)
    # assert not repo_path

    Backups.init_repo()

    # register our service
    services.services.append(service)

    assert get_service_by_id(service.get_id()) is not None
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
    provider = ProviderClass(location=test_repo_path)
    assert provider is not None
    return provider


def test_config_load(generic_userdata):
    Backups.reset(reset_json=False)
    provider = Backups.provider()

    assert provider is not None
    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"
    assert provider.location == "selfprivacy"

    assert provider.backuper.account == "ID"
    assert provider.backuper.key == "KEY"


def test_json_reset(generic_userdata):
    Backups.reset(reset_json=False)
    provider = Backups.provider()
    assert provider is not None
    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"
    assert provider.location == "selfprivacy"

    Backups.reset()
    provider = Backups.provider()
    assert provider is not None
    assert isinstance(provider, AbstractBackupProvider)
    assert provider.login == ""
    assert provider.key == ""
    assert provider.location == ""
    assert provider.repo_id == ""


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_file_backend_init(file_backup):
    file_backup.backuper.init()


def test_backup_simple_file(raw_dummy_service, file_backup):
    # temporarily incomplete
    service = raw_dummy_service
    assert service is not None
    assert file_backup is not None

    name = service.get_id()
    file_backup.backuper.init()


def test_backup_service(dummy_service, backups):
    id = dummy_service.get_id()
    assert_job_finished(f"services.{id}.backup", count=0)
    assert Backups.get_last_backed_up(dummy_service) is None

    Backups.back_up(dummy_service)

    now = datetime.now(timezone.utc)
    date = Backups.get_last_backed_up(dummy_service)
    assert date is not None
    assert now > date
    assert now - date < timedelta(minutes=1)

    assert_job_finished(f"services.{id}.backup", count=1)


def test_no_repo(memory_backup):
    with pytest.raises(ValueError):
        assert memory_backup.backuper.get_snapshots() == []


def test_one_snapshot(backups, dummy_service):
    Backups.back_up(dummy_service)

    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1
    snap = snaps[0]
    assert snap.service_name == dummy_service.get_id()


def test_backup_returns_snapshot(backups, dummy_service):
    service_folders = dummy_service.get_folders()
    provider = Backups.provider()
    name = dummy_service.get_id()
    snapshot = provider.backuper.start_backup(service_folders, name)

    assert snapshot.id is not None
    assert snapshot.service_name == name
    assert snapshot.created_at is not None


def service_files(service):
    result = []
    for service_folder in service.get_folders():
        service_filename = listdir(service_folder)[0]
        assert service_filename is not None
        service_file = path.join(service_folder, service_filename)
        result.append(service_file)
    return result


def test_restore(backups, dummy_service):
    paths_to_nuke = service_files(dummy_service)
    contents = []

    for service_file in paths_to_nuke:
        with open(service_file, "r") as file:
            contents.append(file.read())

    Backups.back_up(dummy_service)
    snap = Backups.get_snapshots(dummy_service)[0]
    assert snap is not None

    for p in paths_to_nuke:
        assert path.exists(p)
        remove(p)
        assert not path.exists(p)

    Backups.restore_service_from_snapshot(dummy_service, snap.id)
    for p, content in zip(paths_to_nuke, contents):
        assert path.exists(p)
        with open(p, "r") as file:
            assert file.read() == content


def test_sizing(backups, dummy_service):
    Backups.back_up(dummy_service)
    snap = Backups.get_snapshots(dummy_service)[0]
    size = Backups.service_snapshot_size(snap.id)
    assert size is not None
    assert size > 0


def test_init_tracking(backups, raw_dummy_service):
    assert Backups.is_initted() is False

    Backups.init_repo()

    assert Backups.is_initted() is True


def finished_jobs():
    return [job for job in Jobs.get_jobs() if job.status is JobStatus.FINISHED]


def assert_job_finished(job_type, count):
    finished_types = [job.type_id for job in finished_jobs()]
    assert finished_types.count(job_type) == count


def assert_job_has_run(job_type):
    job = [job for job in finished_jobs() if job.type_id == job_type][0]
    assert JobStatus.RUNNING in Jobs.status_updates(job)


def assert_job_had_progress(job_type):
    job = [job for job in finished_jobs() if job.type_id == job_type][0]
    assert len(Jobs.progress_updates(job)) > 0


def test_snapshots_by_id(backups, dummy_service):
    snap1 = Backups.back_up(dummy_service)
    snap2 = Backups.back_up(dummy_service)
    snap3 = Backups.back_up(dummy_service)

    assert snap2.id is not None
    assert snap2.id != ""

    assert len(Backups.get_snapshots(dummy_service)) == 3
    assert Backups.get_snapshot_by_id(snap2.id).id == snap2.id


def test_backup_service_task(backups, dummy_service):
    handle = start_backup(dummy_service)
    handle(blocking=True)

    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1

    id = dummy_service.get_id()
    job_type_id = f"services.{id}.backup"
    assert_job_finished(job_type_id, count=1)
    assert_job_has_run(job_type_id)
    assert_job_had_progress(job_type_id)


def test_restore_snapshot_task(backups, dummy_service):
    Backups.back_up(dummy_service)
    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1

    paths_to_nuke = service_files(dummy_service)
    contents = []

    for service_file in paths_to_nuke:
        with open(service_file, "r") as file:
            contents.append(file.read())

    for p in paths_to_nuke:
        remove(p)

    handle = restore_snapshot(snaps[0])
    handle(blocking=True)

    for p, content in zip(paths_to_nuke, contents):
        assert path.exists(p)
        with open(p, "r") as file:
            assert file.read() == content


def test_autobackup_enable_service(backups, dummy_service):
    assert not Backups.is_autobackup_enabled(dummy_service)

    Backups.enable_autobackup(dummy_service)
    assert Backups.is_autobackup_enabled(dummy_service)

    Backups.disable_autobackup(dummy_service)
    assert not Backups.is_autobackup_enabled(dummy_service)


def test_autobackup_enable_service_storage(backups, dummy_service):
    assert len(Storage.services_with_autobackup()) == 0

    Backups.enable_autobackup(dummy_service)
    assert len(Storage.services_with_autobackup()) == 1
    assert Storage.services_with_autobackup()[0] == dummy_service.get_id()

    Backups.disable_autobackup(dummy_service)
    assert len(Storage.services_with_autobackup()) == 0


def test_set_autobackup_period(backups):
    assert Backups.autobackup_period_minutes() is None

    Backups.set_autobackup_period_minutes(2)
    assert Backups.autobackup_period_minutes() == 2

    Backups.disable_all_autobackup()
    assert Backups.autobackup_period_minutes() is None

    Backups.set_autobackup_period_minutes(3)
    assert Backups.autobackup_period_minutes() == 3

    Backups.set_autobackup_period_minutes(0)
    assert Backups.autobackup_period_minutes() is None

    Backups.set_autobackup_period_minutes(3)
    assert Backups.autobackup_period_minutes() == 3

    Backups.set_autobackup_period_minutes(-1)
    assert Backups.autobackup_period_minutes() is None


def test_no_default_autobackup(backups, dummy_service):
    now = datetime.now(timezone.utc)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)


def test_autobackup_timer_periods(backups, dummy_service):
    now = datetime.now(timezone.utc)
    backup_period = 13  # minutes

    Backups.enable_autobackup(dummy_service)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert Backups.is_time_to_backup(now)

    Backups.set_autobackup_period_minutes(0)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)


def test_autobackup_timer_enabling(backups, dummy_service):
    now = datetime.now(timezone.utc)
    backup_period = 13  # minutes

    Backups.set_autobackup_period_minutes(backup_period)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)

    Backups.enable_autobackup(dummy_service)
    assert Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert Backups.is_time_to_backup(now)

    Backups.disable_autobackup(dummy_service)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)


def test_autobackup_timing(backups, dummy_service):
    backup_period = 13  # minutes
    now = datetime.now(timezone.utc)

    Backups.enable_autobackup(dummy_service)
    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert Backups.is_time_to_backup(now)

    Backups.back_up(dummy_service)

    now = datetime.now(timezone.utc)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), now)
    assert not Backups.is_time_to_backup(now)

    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert not Backups.is_time_to_backup_service(dummy_service.get_id(), past)
    assert not Backups.is_time_to_backup(past)

    future = datetime.now(timezone.utc) + timedelta(minutes=backup_period + 2)
    assert Backups.is_time_to_backup_service(dummy_service.get_id(), future)
    assert Backups.is_time_to_backup(future)


# Storage
def test_snapshots_caching(backups, dummy_service):
    Backups.back_up(dummy_service)

    # we test indirectly that we do redis calls instead of shell calls
    start = datetime.now()
    for i in range(10):
        snapshots = Backups.get_snapshots(dummy_service)
        assert len(snapshots) == 1
    assert datetime.now() - start < timedelta(seconds=0.5)

    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1

    Storage.delete_cached_snapshot(cached_snapshots[0])
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0

    snapshots = Backups.get_snapshots(dummy_service)
    assert len(snapshots) == 1
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1


# Storage
def test_init_tracking_caching(backups, raw_dummy_service):
    assert Storage.has_init_mark() is False

    Storage.mark_as_init()

    assert Storage.has_init_mark() is True
    assert Backups.is_initted() is True


# Storage
def test_init_tracking_caching2(backups, raw_dummy_service):
    assert Storage.has_init_mark() is False

    Backups.init_repo()

    assert Storage.has_init_mark() is True


# Storage
def test_provider_storage(backups_backblaze):
    provider = Backups.provider()

    assert provider is not None

    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"

    Storage.store_provider(provider)
    restored_provider = Backups.load_provider_redis()
    assert isinstance(restored_provider, Backblaze)
    assert restored_provider.login == "ID"
    assert restored_provider.key == "KEY"


def test_services_to_back_up(backups, dummy_service):
    backup_period = 13  # minutes
    now = datetime.now(timezone.utc)

    Backups.enable_autobackup(dummy_service)
    Backups.set_autobackup_period_minutes(backup_period)

    services = Backups.services_to_back_up(now)
    assert len(services) == 1
    assert services[0].get_id() == dummy_service.get_id()
