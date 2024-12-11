import pytest

from typing import List

import os
import os.path as path
from os import remove
from os import listdir
from os import urandom

from datetime import datetime, timedelta, timezone
import tempfile

from selfprivacy_api.utils.huey import huey

from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.services import ServiceManager

from selfprivacy_api.graphql.queries.providers import BackupProvider as ProviderEnum
from selfprivacy_api.graphql.common_types.backup import (
    RestoreStrategy,
    BackupReason,
)
from selfprivacy_api.graphql.queries.providers import BackupProvider

from selfprivacy_api.jobs import Job, Jobs, JobStatus

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.backup import Backups, BACKUP_PROVIDER_ENVS
import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider
from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.backup.providers.none import NoBackups
from selfprivacy_api.backup.providers import get_kind
from selfprivacy_api.backup.util import sync

from selfprivacy_api.backup.tasks import (
    start_backup,
    restore_snapshot,
    reload_snapshot_cache,
    total_backup,
    do_full_restore,
    which_snapshots_to_full_restore,
)
from selfprivacy_api.backup.storage import Storage
from selfprivacy_api.backup.local_secret import LocalBackupSecret
from selfprivacy_api.backup.jobs import (
    get_backup_fail,
    add_total_backup_job,
    add_total_restore_job,
)

from tests.common import assert_job_errored
from tests.conftest import (
    write_testfile_bodies,
    get_testfile_bodies,
    assert_original_files,
    assert_rebuild_was_made,
)
from tests.test_dkim import dkim_file

from tests.test_graphql.test_services import (
    only_dummy_service_and_api,
    only_dummy_service,
)

REPO_NAME = "test_backup"

REPOFILE_NAME = "totallyunrelated"


def prepare_localfile_backups(temp_dir):
    test_repo_path = path.join(temp_dir, REPOFILE_NAME)
    assert not path.exists(test_repo_path)
    Backups.set_localfile_repo(test_repo_path)


@pytest.fixture(scope="function")
def backups_local(tmpdir):
    Backups.reset()
    prepare_localfile_backups(tmpdir)
    Jobs.reset()
    Backups.init_repo()


@pytest.fixture(scope="function")
def backups(tmpdir):
    """
    For those tests that are supposed to pass with
    both local and cloud repos
    """

    # Sometimes this is false. Idk why.
    huey.immediate = True
    assert huey.immediate is True

    Backups.reset()
    if BACKUP_PROVIDER_ENVS["kind"] in os.environ.keys():
        Backups.set_provider_from_envs()
    else:
        prepare_localfile_backups(tmpdir)
    Jobs.reset()

    Backups.init_repo()
    assert Backups.provider().location == str(tmpdir) + "/" + REPOFILE_NAME
    yield
    Backups.erase_repo()


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


def ids(snapshots: List[Snapshot]) -> List[str]:
    return [snapshot.id for snapshot in snapshots]


def assert_job_ok(job: Job):
    try:
        assert job.status == JobStatus.FINISHED
    # For easier debug
    except AssertionError:
        raise ValueError("Job errored out when it was not supposed to:", job.error)


def test_reset_sets_to_none1():
    Backups.reset()
    provider = Backups.provider()
    assert provider is not None
    assert isinstance(provider, NoBackups)


def test_reset_sets_to_none2(backups):
    # now with something set up first^^^
    Backups.reset()
    provider = Backups.provider()
    assert provider is not None
    assert isinstance(provider, NoBackups)


def test_setting_from_envs(tmpdir):
    Backups.reset()
    environment_stash = {}
    if BACKUP_PROVIDER_ENVS["kind"] in os.environ.keys():
        # we are running under special envs, stash them before rewriting them
        for key in BACKUP_PROVIDER_ENVS.values():
            environment_stash[key] = os.environ[key]

    os.environ[BACKUP_PROVIDER_ENVS["kind"]] = "BACKBLAZE"
    os.environ[BACKUP_PROVIDER_ENVS["login"]] = "ID"
    os.environ[BACKUP_PROVIDER_ENVS["key"]] = "KEY"
    os.environ[BACKUP_PROVIDER_ENVS["location"]] = "selfprivacy"
    Backups.set_provider_from_envs()
    provider = Backups.provider()

    assert provider is not None
    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"
    assert provider.location == "selfprivacy"

    assert provider.backupper.account == "ID"
    assert provider.backupper.key == "KEY"

    if environment_stash != {}:
        for key in BACKUP_PROVIDER_ENVS.values():
            os.environ[key] = environment_stash[key]
    else:
        for key in BACKUP_PROVIDER_ENVS.values():
            del os.environ[key]


def test_select_backend():
    provider = providers.get_provider(BackupProvider.BACKBLAZE)
    assert provider is not None
    assert provider == Backblaze


def test_file_backend_init(file_backup):
    file_backup.backupper.init()


def test_reinit_after_purge(backups):
    assert Backups.is_initted() is True

    Backups.erase_repo()
    assert Backups.is_initted() is False
    with pytest.raises(ValueError):
        Backups.force_snapshot_cache_reload()

    Backups.init_repo()
    assert Backups.is_initted() is True
    assert len(Backups.get_all_snapshots()) == 0


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


def all_job_text(job: Job) -> str:
    # Use when we update to pydantic 2.xxx
    # return Job.model_dump_json()
    result = ""
    if job.status_text is not None:
        result += job.status_text
    if job.description is not None:
        result += job.description
    if job.error is not None:
        result += job.error

    return result


def test_error_censoring_encryptionkey(dummy_service, backups):
    # Discard our key to inject a failure
    old_key = LocalBackupSecret.get()
    LocalBackupSecret.reset()
    new_key = LocalBackupSecret.get()

    with pytest.raises(ValueError):
        # Should fail without correct key
        Backups.back_up(dummy_service)

    job = get_backup_fail(dummy_service)
    assert_job_errored(job)

    job_text = all_job_text(job)

    assert old_key not in job_text
    assert new_key not in job_text
    # local backups do not have login key
    # assert Backups.provider().key not in job_text

    assert "CENSORED" in job_text


def test_error_censoring_loginkey(dummy_service, backups, fp):
    # We do not want to screw up our teardown
    old_provider = Backups.provider()

    secret = "aSecretNYA"

    Backups.set_provider(
        ProviderEnum.BACKBLAZE, login="meow", key=secret, location="moon"
    )
    assert Backups.provider().key == secret

    # We could have called real backblaze but it is kind of not privacy so.
    fp.allow_unregistered(True)
    fp.register(
        ["restic", fp.any()],
        returncode=1,
        stdout="only real cats are allowed",
        # We do not want to suddenly call real backblaze even if code changes
        occurrences=100,
    )

    with pytest.raises(ValueError):
        Backups.back_up(dummy_service)

    job = get_backup_fail(dummy_service)
    assert_job_errored(job)

    job_text = all_job_text(job)
    assert secret not in job_text
    assert job_text.count("CENSORED") == 2

    # We do not want to screw up our teardown
    Storage.store_provider(old_provider)


def test_no_repo(memory_backup):
    with pytest.raises(ValueError):
        assert memory_backup.backupper.get_snapshots() == []


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
    snapshot = provider.backupper.start_backup(service_folders, name)

    assert snapshot.id is not None

    snapshots = provider.backupper.get_snapshots()
    assert snapshots != []

    assert len(snapshot.id) == len(snapshots[0].id)
    assert Backups.get_snapshot_by_id(snapshot.id) is not None
    assert snapshot.service_name == name
    assert snapshot.created_at is not None
    assert snapshot.reason == BackupReason.EXPLICIT


def test_backup_reasons(backups, dummy_service):
    snap = Backups.back_up(dummy_service, BackupReason.AUTO)
    assert snap.reason == BackupReason.AUTO

    Backups.force_snapshot_cache_reload()
    snaps = Backups.get_snapshots(dummy_service)
    assert snaps[0].reason == BackupReason.AUTO


def folder_files(folder):
    return [
        path.join(folder, filename)
        for filename in listdir(folder)
        if filename is not None
    ]


def service_files(service):
    result = []
    for service_folder in service.get_folders():
        result.extend(folder_files(service_folder))
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

    Backups._restore_service_from_snapshot(dummy_service, snap.id)
    for p, content in zip(paths_to_nuke, contents):
        assert path.exists(p)
        with open(p, "r") as file:
            assert file.read() == content


def test_sizing(backups, dummy_service):
    Backups.back_up(dummy_service)
    snap = Backups.get_snapshots(dummy_service)[0]
    size = Backups.snapshot_restored_size(snap.id)
    assert size is not None
    assert size > 0


def test_init_tracking(backups, tmpdir):
    assert Backups.is_initted() is True
    Backups.reset()
    assert Backups.is_initted() is False
    separate_dir = tmpdir / "out_of_the_way"
    prepare_localfile_backups(separate_dir)
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


def job_progress_updates(job_type):
    job = [job for job in finished_jobs() if job.type_id == job_type][0]
    return Jobs.progress_updates(job)


def assert_job_had_progress(job_type):
    assert len(job_progress_updates(job_type)) > 0


def make_large_file(path: str, bytes: int):
    with open(path, "wb") as file:
        file.write(urandom(bytes))


def test_snapshots_by_id(backups, dummy_service):
    snap1 = Backups.back_up(dummy_service)
    snap2 = Backups.back_up(dummy_service)
    snap3 = Backups.back_up(dummy_service)

    assert snap2.id is not None
    assert snap2.id != ""

    assert len(Backups.get_snapshots(dummy_service)) == 3
    assert Backups.get_snapshot_by_id(snap2.id).id == snap2.id


@pytest.fixture(params=["instant_server_stop", "delayed_server_stop"])
def simulated_service_stopping_delay(request) -> float:
    if request.param == "instant_server_stop":
        return 0.0
    else:
        return 0.3


def test_backup_service_task(backups, dummy_service, simulated_service_stopping_delay):
    dummy_service.set_delay(simulated_service_stopping_delay)

    handle = start_backup(dummy_service.get_id())
    handle(blocking=True)

    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1

    id = dummy_service.get_id()
    job_type_id = f"services.{id}.backup"
    assert_job_finished(job_type_id, count=1)
    assert_job_has_run(job_type_id)
    assert_job_had_progress(job_type_id)


def test_forget_snapshot(backups, dummy_service):
    snap1 = Backups.back_up(dummy_service)
    snap2 = Backups.back_up(dummy_service)
    assert len(Backups.get_snapshots(dummy_service)) == 2

    Backups.forget_snapshot(snap2)
    assert len(Backups.get_snapshots(dummy_service)) == 1
    Backups.force_snapshot_cache_reload()
    assert len(Backups.get_snapshots(dummy_service)) == 1

    assert Backups.get_snapshots(dummy_service)[0].id == snap1.id

    Backups.forget_snapshot(snap1)
    assert len(Backups.get_snapshots(dummy_service)) == 0


def test_forget_nonexistent_snapshot(backups, dummy_service):
    bogus = Snapshot(
        id="gibberjibber",
        service_name="nohoho",
        created_at=datetime.now(timezone.utc),
        reason=BackupReason.EXPLICIT,
    )
    with pytest.raises(ValueError):
        Backups.forget_snapshot(bogus)


def test_backup_larger_file(backups, dummy_service):
    dir = path.join(dummy_service.get_folders()[0], "LARGEFILE")
    mega = 2**20
    make_large_file(dir, 100 * mega)

    handle = start_backup(dummy_service.get_id())
    handle(blocking=True)

    # results will be slightly different on different machines. if someone has troubles with it on their machine, consider dropping this test.
    id = dummy_service.get_id()
    job_type_id = f"services.{id}.backup"
    assert_job_finished(job_type_id, count=1)
    assert_job_has_run(job_type_id)
    updates = job_progress_updates(job_type_id)
    assert len(updates) > 3
    assert updates[int((len(updates) - 1) / 2.0)] > 10
    # clean up a bit
    remove(dir)


@pytest.fixture(params=["verify", "inplace"])
def restore_strategy(request) -> RestoreStrategy:
    if request.param == "verify":
        return RestoreStrategy.DOWNLOAD_VERIFY_OVERWRITE
    else:
        return RestoreStrategy.INPLACE


@pytest.fixture(params=["failed", "healthy", "fail_to_stop"])
def failed(request) -> str:
    return request.param


def test_restore_snapshot_task(
    backups, dummy_service, restore_strategy, simulated_service_stopping_delay, failed
):
    dummy_service.set_delay(simulated_service_stopping_delay)
    if failed == "failed":
        dummy_service.set_status(ServiceStatus.FAILED)

    if failed == "fail_to_stop":
        dummy_service.simulate_fail_to_stop(True)

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

    handle = restore_snapshot(snaps[0], restore_strategy)
    handle(blocking=True)

    for p, content in zip(paths_to_nuke, contents):
        assert path.exists(p)
        with open(p, "r") as file:
            assert file.read() == content

    snaps = Backups.get_snapshots(dummy_service)
    if restore_strategy == RestoreStrategy.INPLACE:
        assert len(snaps) == 2
        reasons = [snap.reason for snap in snaps]
        assert BackupReason.PRE_RESTORE in reasons
    else:
        assert len(snaps) == 1


def test_backup_unbackuppable(backups, dummy_service):
    dummy_service.set_backuppable(False)
    assert dummy_service.can_be_backed_up() is False
    with pytest.raises(ValueError):
        Backups.back_up(dummy_service)


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

    snap_to_uncache = cached_snapshots[0]
    Storage.delete_cached_snapshot(snap_to_uncache)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0

    # We do not assume that no snapshots means we need to reload the cache
    snapshots = Backups.get_snapshots(dummy_service)
    assert len(snapshots) == 0
    # No cache reload happened
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0


# Storage
def test_snapshot_cache_autoreloads(backups, dummy_service):
    Backups.back_up(dummy_service)

    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1
    snap_to_uncache = cached_snapshots[0]

    Storage.delete_cached_snapshot(snap_to_uncache)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0

    # When we create a snapshot we do reload cache
    Backups.back_up(dummy_service)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 2
    assert snap_to_uncache in cached_snapshots

    Storage.delete_cached_snapshot(snap_to_uncache)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1

    # When we try to delete a snapshot we cannot find in cache, it is ok and we do reload cache
    Backups.forget_snapshot(snap_to_uncache)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1
    assert snap_to_uncache not in cached_snapshots


def lowlevel_forget(snapshot_id):
    Backups.provider().backupper.forget_snapshot(snapshot_id)


# Storage
def test_snapshots_cache_invalidation(backups, dummy_service):
    Backups.back_up(dummy_service)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1

    Storage.invalidate_snapshot_storage()
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0

    Backups.force_snapshot_cache_reload()
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1
    snap = cached_snapshots[0]

    lowlevel_forget(snap.id)
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 1

    Backups.force_snapshot_cache_reload()
    cached_snapshots = Storage.get_cached_snapshots()
    assert len(cached_snapshots) == 0


# Storage
def test_init_tracking_caching(backups, raw_dummy_service):
    assert Storage.has_init_mark() is True
    Backups.reset()
    assert Storage.has_init_mark() is False

    Storage.mark_as_init()

    assert Storage.has_init_mark() is True
    assert Backups.is_initted() is True


# Storage
def test_init_tracking_caching2(backups, tmpdir):
    assert Storage.has_init_mark() is True
    Backups.reset()
    assert Storage.has_init_mark() is False
    separate_dir = tmpdir / "out_of_the_way"
    prepare_localfile_backups(separate_dir)
    assert Storage.has_init_mark() is False

    Backups.init_repo()

    assert Storage.has_init_mark() is True


# Storage
def test_provider_storage(backups):
    test_login = "ID"
    test_key = "KEY"
    test_location = "selprivacy_bin"

    old_provider = Backups.provider()
    assert old_provider is not None

    assert not isinstance(old_provider, Backblaze)
    assert old_provider.login != test_login
    assert old_provider.key != test_key
    assert old_provider.location != test_location

    test_provider = Backups._construct_provider(
        kind=BackupProvider.BACKBLAZE, login="ID", key=test_key, location=test_location
    )

    assert isinstance(test_provider, Backblaze)
    assert get_kind(test_provider) == "BACKBLAZE"
    assert test_provider.login == test_login
    assert test_provider.key == test_key
    assert test_provider.location == test_location

    Storage.store_provider(test_provider)

    restored_provider_model = Storage.load_provider()
    assert restored_provider_model.kind == "BACKBLAZE"
    assert restored_provider_model.login == test_login
    assert restored_provider_model.key == test_key
    assert restored_provider_model.location == test_location

    restored_provider = Backups._load_provider_redis()
    assert isinstance(restored_provider, Backblaze)
    assert restored_provider.login == test_login
    assert restored_provider.key == test_key
    assert restored_provider.location == test_location

    # Revert our mess so we can teardown ok
    Storage.store_provider(old_provider)


def test_sync(dummy_service):
    src = dummy_service.get_folders()[0]
    dst = dummy_service.get_folders()[1]
    old_files_src = set(listdir(src))
    old_files_dst = set(listdir(dst))
    assert old_files_src != old_files_dst

    sync(src, dst)
    new_files_src = set(listdir(src))
    new_files_dst = set(listdir(dst))
    assert new_files_src == old_files_src
    assert new_files_dst == new_files_src


def test_sync_nonexistent_src(dummy_service):
    src = "/var/lib/nonexistentFluffyBunniesOfUnix"
    dst = dummy_service.get_folders()[1]

    with pytest.raises(ValueError):
        sync(src, dst)


def test_move_blocks_backups(backups, dummy_service, restore_strategy):
    snap = Backups.back_up(dummy_service)
    job = Jobs.add(
        type_id=f"services.{dummy_service.get_id()}.move",
        name="Move Dummy",
        description=f"Moving Dummy data to the Rainbow Land",
        status=JobStatus.RUNNING,
    )

    with pytest.raises(ValueError):
        Backups.back_up(dummy_service)

    with pytest.raises(ValueError):
        Backups.restore_snapshot(snap, restore_strategy)


def test_double_lock_unlock(backups, dummy_service):
    # notice that introducing stale locks is only safe for other tests if we erase repo in between
    # which we do at the time of writing this test

    Backups.provider().backupper.lock()
    with pytest.raises(ValueError):
        Backups.provider().backupper.lock()

    Backups.provider().backupper.unlock()
    Backups.provider().backupper.lock()

    Backups.provider().backupper.unlock()
    Backups.provider().backupper.unlock()


def test_operations_while_locked(backups, dummy_service):
    # Stale lock prevention test

    # consider making it fully at the level of backupper?
    # because this is where prevention lives?
    # Backups singleton is here only so that we can run this against B2, S3 and whatever
    # But maybe it is not necessary (if restic treats them uniformly enough)

    Backups.provider().backupper.lock()
    snap = Backups.back_up(dummy_service)
    assert snap is not None

    Backups.provider().backupper.lock()
    # using lowlevel to make sure no caching interferes
    assert Backups.provider().backupper.is_initted() is True

    Backups.provider().backupper.lock()
    assert Backups.snapshot_restored_size(snap.id) > 0

    Backups.provider().backupper.lock()
    Backups.restore_snapshot(snap)

    Backups.provider().backupper.lock()
    Backups.forget_snapshot(snap)

    Backups.provider().backupper.lock()
    assert Backups.provider().backupper.get_snapshots() == []

    # check that no locks were left
    Backups.provider().backupper.lock()
    Backups.provider().backupper.unlock()


# a paranoid check to weed out problems with tempdirs that are not dependent on us
def test_tempfile():
    with tempfile.TemporaryDirectory() as temp:
        assert path.exists(temp)
    assert not path.exists(temp)


# Storage
def test_cache_invalidaton_task(backups, dummy_service):
    Backups.back_up(dummy_service)
    assert len(Storage.get_cached_snapshots()) == 1

    # Does not trigger resync
    Storage.invalidate_snapshot_storage()
    assert Storage.get_cached_snapshots() == []

    reload_snapshot_cache()
    assert len(Storage.get_cached_snapshots()) == 1


def test_service_manager_backup_snapshot_persists(backups, generic_userdata, dkim_file):
    # There was a bug with snapshot disappearance due to post_restore hooks, checking for that
    manager = ServiceManager.get_service_by_id(ServiceManager.get_id())
    assert manager is not None

    snapshot = Backups.back_up(manager)

    Backups.force_snapshot_cache_reload()
    ids = [snap.id for snap in Backups.get_all_snapshots()]
    assert snapshot.id in ids


def test_service_manager_backs_up_without_crashing(
    backups, generic_userdata, dkim_file, dummy_service
):
    """
    Service manager is special and needs testing.
    """
    manager = ServiceManager.get_service_by_id(ServiceManager.get_id())
    assert manager is not None

    snapshot = Backups.back_up(manager)
    Backups.restore_snapshot(snapshot)


def test_backup_all_restore_all(
    backups,
    generic_userdata,
    dkim_file,
    only_dummy_service_and_api,
    catch_nixos_rebuild_calls,
):
    dummy_service = only_dummy_service_and_api
    fp = catch_nixos_rebuild_calls
    fp.pass_command(["restic", fp.any()])
    fp.keep_last_process(True)
    fp.pass_command(["rclone", fp.any()])
    fp.keep_last_process(True)
    fp.pass_command(["lsblk", fp.any()])
    fp.keep_last_process(True)

    assert len(Backups.get_all_snapshots()) == 0

    backup_job = add_total_backup_job()
    total_backup(backup_job)
    assert len(Backups.get_all_snapshots()) == 2

    assert set(ids(which_snapshots_to_full_restore())) == set(
        ids(Backups.get_all_snapshots())
    )

    write_testfile_bodies(dummy_service, ["bogus", "bleeegh corruption ><"])

    restore_job = add_total_restore_job()

    do_full_restore(restore_job)
    assert_job_ok(restore_job)

    assert_rebuild_was_made(fp)
    assert_original_files(dummy_service)
