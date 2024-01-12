import pytest

import os
import os.path as path
from os import remove
from os import listdir
from os import urandom

from datetime import datetime, timedelta, timezone
from copy import copy
import tempfile

from selfprivacy_api.utils.huey import huey

import tempfile

from selfprivacy_api.utils.huey import huey

from selfprivacy_api.services import Service, get_all_services
from selfprivacy_api.services import get_service_by_id
from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.services.test_service import DummyService

from selfprivacy_api.graphql.queries.providers import BackupProvider
from selfprivacy_api.graphql.common_types.backup import (
    RestoreStrategy,
    BackupReason,
    AutobackupQuotas,
)

from selfprivacy_api.jobs import Jobs, JobStatus

from selfprivacy_api.models.backup.snapshot import Snapshot

from selfprivacy_api.backup import Backups, BACKUP_PROVIDER_ENVS
import selfprivacy_api.backup.providers as providers
from selfprivacy_api.backup.providers import AbstractBackupProvider
from selfprivacy_api.backup.providers.backblaze import Backblaze
from selfprivacy_api.backup.providers.none import NoBackups
from selfprivacy_api.backup.util import sync

from selfprivacy_api.backup.tasks import (
    start_backup,
    restore_snapshot,
    reload_snapshot_cache,
    prune_autobackup_snapshots,
)
from selfprivacy_api.backup.storage import Storage


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
def backups_backblaze(generic_userdata):
    Backups.reset(reset_json=False)


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

    assert provider.backupper.account == "ID"
    assert provider.backupper.key == "KEY"


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
    file_backup.backupper.init()


def test_reinit_after_purge(backups):
    assert Backups.is_initted() is True

    Backups.erase_repo()
    assert Backups.is_initted() is False
    with pytest.raises(ValueError):
        Backups.get_all_snapshots()

    Backups.init_repo()
    assert Backups.is_initted() is True
    assert len(Backups.get_all_snapshots()) == 0


def test_backup_simple_file(raw_dummy_service, file_backup):
    # temporarily incomplete
    service = raw_dummy_service
    assert service is not None
    assert file_backup is not None

    name = service.get_id()
    file_backup.backupper.init()


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
    assert len(snapshot.id) == len(Backups.get_all_snapshots()[0].id)
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


unlimited_quotas = AutobackupQuotas(
    last=-1,
    daily=-1,
    weekly=-1,
    monthly=-1,
    yearly=-1,
)

zero_quotas = AutobackupQuotas(
    last=0,
    daily=0,
    weekly=0,
    monthly=0,
    yearly=0,
)


def test_get_empty_quotas(backups):
    quotas = Backups.autobackup_quotas()
    assert quotas is not None
    assert quotas == unlimited_quotas


def test_set_quotas(backups):
    quotas = AutobackupQuotas(
        last=3,
        daily=2343,
        weekly=343,
        monthly=0,
        yearly=-34556,
    )
    Backups.set_autobackup_quotas(quotas)
    assert Backups.autobackup_quotas() == AutobackupQuotas(
        last=3,
        daily=2343,
        weekly=343,
        monthly=0,
        yearly=-1,
    )


def test_set_zero_quotas(backups):
    quotas = AutobackupQuotas(
        last=0,
        daily=0,
        weekly=0,
        monthly=0,
        yearly=0,
    )
    Backups.set_autobackup_quotas(quotas)
    assert Backups.autobackup_quotas() == zero_quotas


def test_set_unlimited_quotas(backups):
    quotas = AutobackupQuotas(
        last=-1,
        daily=-1,
        weekly=-1,
        monthly=-1,
        yearly=-1,
    )
    Backups.set_autobackup_quotas(quotas)
    assert Backups.autobackup_quotas() == unlimited_quotas


def test_set_zero_quotas_after_unlimited(backups):
    quotas = AutobackupQuotas(
        last=-1,
        daily=-1,
        weekly=-1,
        monthly=-1,
        yearly=-1,
    )
    Backups.set_autobackup_quotas(quotas)
    assert Backups.autobackup_quotas() == unlimited_quotas

    quotas = AutobackupQuotas(
        last=0,
        daily=0,
        weekly=0,
        monthly=0,
        yearly=0,
    )
    Backups.set_autobackup_quotas(quotas)
    assert Backups.autobackup_quotas() == zero_quotas


def dummy_snapshot(date: datetime):
    return Snapshot(
        id=str(hash(date)),
        service_name="someservice",
        created_at=date,
        reason=BackupReason.EXPLICIT,
    )


def test_autobackup_snapshots_pruning(backups):
    # Wednesday, fourth week
    now = datetime(year=2023, month=1, day=25, hour=10)

    snaps = [
        dummy_snapshot(now),
        dummy_snapshot(now - timedelta(minutes=5)),
        dummy_snapshot(now - timedelta(hours=2)),
        dummy_snapshot(now - timedelta(hours=5)),
        dummy_snapshot(now - timedelta(days=1)),
        dummy_snapshot(now - timedelta(days=1, hours=2)),
        dummy_snapshot(now - timedelta(days=1, hours=3)),
        dummy_snapshot(now - timedelta(days=2)),
        dummy_snapshot(now - timedelta(days=7)),
        dummy_snapshot(now - timedelta(days=12)),
        dummy_snapshot(now - timedelta(days=23)),
        dummy_snapshot(now - timedelta(days=28)),
        dummy_snapshot(now - timedelta(days=32)),
        dummy_snapshot(now - timedelta(days=47)),
        dummy_snapshot(now - timedelta(days=64)),
        dummy_snapshot(now - timedelta(days=84)),
        dummy_snapshot(now - timedelta(days=104)),
        dummy_snapshot(now - timedelta(days=365 * 2)),
    ]
    old_len = len(snaps)

    quotas = copy(unlimited_quotas)
    Backups.set_autobackup_quotas(quotas)
    assert Backups._prune_snaps_with_quotas(snaps) == snaps

    quotas = copy(zero_quotas)
    quotas.last = 2
    quotas.daily = 2
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(now),
        dummy_snapshot(now - timedelta(minutes=5)),
        # dummy_snapshot(now - timedelta(hours=2)),
        # dummy_snapshot(now - timedelta(hours=5)),
        dummy_snapshot(now - timedelta(days=1)),
        # dummy_snapshot(now - timedelta(days=1, hours=2)),
        # dummy_snapshot(now - timedelta(days=1, hours=3)),
        # dummy_snapshot(now - timedelta(days=2)),
        # dummy_snapshot(now - timedelta(days=7)),
        # dummy_snapshot(now - timedelta(days=12)),
        # dummy_snapshot(now - timedelta(days=23)),
        # dummy_snapshot(now - timedelta(days=28)),
        # dummy_snapshot(now - timedelta(days=32)),
        # dummy_snapshot(now - timedelta(days=47)),
        # dummy_snapshot(now - timedelta(days=64)),
        # dummy_snapshot(now - timedelta(days=84)),
        # dummy_snapshot(now - timedelta(days=104)),
        # dummy_snapshot(now - timedelta(days=365 * 2)),
    ]

    # checking that this function does not mutate the argument
    assert snaps != snaps_to_keep
    assert len(snaps) == old_len

    quotas = copy(zero_quotas)
    quotas.weekly = 4
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(now),
        # dummy_snapshot(now - timedelta(minutes=5)),
        # dummy_snapshot(now - timedelta(hours=2)),
        # dummy_snapshot(now - timedelta(hours=5)),
        # dummy_snapshot(now - timedelta(days=1)),
        # dummy_snapshot(now - timedelta(days=1, hours=2)),
        # dummy_snapshot(now - timedelta(days=1, hours=3)),
        # dummy_snapshot(now - timedelta(days=2)),
        dummy_snapshot(now - timedelta(days=7)),
        dummy_snapshot(now - timedelta(days=12)),
        dummy_snapshot(now - timedelta(days=23)),
        # dummy_snapshot(now - timedelta(days=28)),
        # dummy_snapshot(now - timedelta(days=32)),
        # dummy_snapshot(now - timedelta(days=47)),
        # dummy_snapshot(now - timedelta(days=64)),
        # dummy_snapshot(now - timedelta(days=84)),
        # dummy_snapshot(now - timedelta(days=104)),
        # dummy_snapshot(now - timedelta(days=365 * 2)),
    ]

    quotas = copy(zero_quotas)
    quotas.monthly = 7
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(now),
        # dummy_snapshot(now - timedelta(minutes=5)),
        # dummy_snapshot(now - timedelta(hours=2)),
        # dummy_snapshot(now - timedelta(hours=5)),
        # dummy_snapshot(now - timedelta(days=1)),
        # dummy_snapshot(now - timedelta(days=1, hours=2)),
        # dummy_snapshot(now - timedelta(days=1, hours=3)),
        # dummy_snapshot(now - timedelta(days=2)),
        # dummy_snapshot(now - timedelta(days=7)),
        # dummy_snapshot(now - timedelta(days=12)),
        # dummy_snapshot(now - timedelta(days=23)),
        dummy_snapshot(now - timedelta(days=28)),
        # dummy_snapshot(now - timedelta(days=32)),
        # dummy_snapshot(now - timedelta(days=47)),
        dummy_snapshot(now - timedelta(days=64)),
        # dummy_snapshot(now - timedelta(days=84)),
        dummy_snapshot(now - timedelta(days=104)),
        dummy_snapshot(now - timedelta(days=365 * 2)),
    ]


def test_autobackup_snapshots_pruning_yearly(backups):
    snaps = [
        dummy_snapshot(datetime(year=2055, month=3, day=1)),
        dummy_snapshot(datetime(year=2055, month=2, day=1)),
        dummy_snapshot(datetime(year=2023, month=4, day=1)),
        dummy_snapshot(datetime(year=2023, month=3, day=1)),
        dummy_snapshot(datetime(year=2023, month=2, day=1)),
        dummy_snapshot(datetime(year=2021, month=2, day=1)),
    ]
    quotas = copy(zero_quotas)
    quotas.yearly = 2
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(datetime(year=2055, month=3, day=1)),
        dummy_snapshot(datetime(year=2023, month=4, day=1)),
    ]


def test_autobackup_snapshots_pruning_bottleneck(backups):
    now = datetime(year=2023, month=1, day=25, hour=10)
    snaps = [
        dummy_snapshot(now),
        dummy_snapshot(now - timedelta(minutes=5)),
        dummy_snapshot(now - timedelta(hours=2)),
        dummy_snapshot(now - timedelta(hours=3)),
        dummy_snapshot(now - timedelta(hours=4)),
    ]

    yearly_quota = copy(zero_quotas)
    yearly_quota.yearly = 2

    monthly_quota = copy(zero_quotas)
    monthly_quota.monthly = 2

    weekly_quota = copy(zero_quotas)
    weekly_quota.weekly = 2

    daily_quota = copy(zero_quotas)
    daily_quota.daily = 2

    last_quota = copy(zero_quotas)
    last_quota.last = 1
    last_quota.yearly = 2

    for quota in [last_quota, yearly_quota, monthly_quota, weekly_quota, daily_quota]:
        print(quota)
        Backups.set_autobackup_quotas(quota)
        snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
        assert snaps_to_keep == [
            dummy_snapshot(now),
            # If there is a vacant quota, we should keep the last snapshot even if it doesn't fit
            dummy_snapshot(now - timedelta(hours=4)),
        ]


def test_autobackup_snapshots_pruning_edgeweek(backups):
    # jan 1 2023 is Sunday
    snaps = [
        dummy_snapshot(datetime(year=2023, month=1, day=6)),
        dummy_snapshot(datetime(year=2023, month=1, day=1)),
        dummy_snapshot(datetime(year=2022, month=12, day=31)),
        dummy_snapshot(datetime(year=2022, month=12, day=30)),
    ]
    quotas = copy(zero_quotas)
    quotas.weekly = 2
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(datetime(year=2023, month=1, day=6)),
        dummy_snapshot(datetime(year=2023, month=1, day=1)),
    ]


def test_autobackup_snapshots_pruning_big_gap(backups):
    snaps = [
        dummy_snapshot(datetime(year=2023, month=1, day=6)),
        dummy_snapshot(datetime(year=2023, month=1, day=2)),
        dummy_snapshot(datetime(year=2022, month=10, day=31)),
        dummy_snapshot(datetime(year=2022, month=10, day=30)),
    ]
    quotas = copy(zero_quotas)
    quotas.weekly = 2
    Backups.set_autobackup_quotas(quotas)

    snaps_to_keep = Backups._prune_snaps_with_quotas(snaps)
    assert snaps_to_keep == [
        dummy_snapshot(datetime(year=2023, month=1, day=6)),
        dummy_snapshot(datetime(year=2022, month=10, day=31)),
    ]


def test_too_many_auto(backups, dummy_service):
    assert Backups.autobackup_quotas()
    quota = copy(zero_quotas)
    quota.last = 2
    Backups.set_autobackup_quotas(quota)
    assert Backups.autobackup_quotas().last == 2

    snap = Backups.back_up(dummy_service, BackupReason.AUTO)
    assert len(Backups.get_snapshots(dummy_service)) == 1
    snap2 = Backups.back_up(dummy_service, BackupReason.AUTO)
    assert len(Backups.get_snapshots(dummy_service)) == 2
    snap3 = Backups.back_up(dummy_service, BackupReason.AUTO)
    assert len(Backups.get_snapshots(dummy_service)) == 2

    snaps = Backups.get_snapshots(dummy_service)
    assert snap2 in snaps
    assert snap3 in snaps
    assert snap not in snaps

    quota.last = -1
    Backups.set_autobackup_quotas(quota)
    snap4 = Backups.back_up(dummy_service, BackupReason.AUTO)

    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 3
    assert snap4 in snaps

    # Retroactivity
    quota.last = 1
    Backups.set_autobackup_quotas(quota)
    job = Jobs.add("trimming", "test.autobackup_trimming", "trimming the snaps!")
    handle = prune_autobackup_snapshots(job)
    handle(blocking=True)
    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1

    snap5 = Backups.back_up(dummy_service, BackupReason.AUTO)
    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 1
    assert snap5 in snaps

    # Explicit snaps are not affected
    snap6 = Backups.back_up(dummy_service, BackupReason.EXPLICIT)

    snaps = Backups.get_snapshots(dummy_service)
    assert len(snaps) == 2
    assert snap5 in snaps
    assert snap6 in snaps


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


@pytest.fixture(params=["failed", "healthy"])
def failed(request) -> bool:
    if request.param == "failed":
        return True
    return False


def test_restore_snapshot_task(
    backups, dummy_service, restore_strategy, simulated_service_stopping_delay, failed
):
    dummy_service.set_delay(simulated_service_stopping_delay)
    if failed:
        dummy_service.set_status(ServiceStatus.FAILED)

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
    assert not Backups.is_time_to_backup_service(dummy_service, now)
    assert not Backups.is_time_to_backup(now)


def backuppable_services() -> list[Service]:
    return [service for service in get_all_services() if service.can_be_backed_up()]


def test_services_to_autobackup(backups, dummy_service):
    backup_period = 13  # minutes
    now = datetime.now(timezone.utc)

    dummy_service.set_backuppable(False)
    services = Backups.services_to_back_up(now)
    assert len(services) == 0

    dummy_service.set_backuppable(True)

    services = Backups.services_to_back_up(now)
    assert len(services) == 0

    Backups.set_autobackup_period_minutes(backup_period)

    services = Backups.services_to_back_up(now)
    assert len(services) == len(backuppable_services())
    assert dummy_service.get_id() in [
        service.get_id() for service in backuppable_services()
    ]


def test_do_not_autobackup_disabled_services(backups, dummy_service):
    now = datetime.now(timezone.utc)
    Backups.set_autobackup_period_minutes(3)
    assert Backups.is_time_to_backup_service(dummy_service, now) is True

    dummy_service.disable()
    assert Backups.is_time_to_backup_service(dummy_service, now) is False


def test_autobackup_timer_periods(backups, dummy_service):
    now = datetime.now(timezone.utc)
    backup_period = 13  # minutes

    assert not Backups.is_time_to_backup_service(dummy_service, now)
    assert not Backups.is_time_to_backup(now)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service, now)
    assert Backups.is_time_to_backup(now)

    Backups.set_autobackup_period_minutes(0)
    assert not Backups.is_time_to_backup_service(dummy_service, now)
    assert not Backups.is_time_to_backup(now)


def test_autobackup_timer_enabling(backups, dummy_service):
    now = datetime.now(timezone.utc)
    backup_period = 13  # minutes
    dummy_service.set_backuppable(False)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup(
        now
    )  # there are other services too, not just our dummy

    # not backuppable service is not backuppable even if period is set
    assert not Backups.is_time_to_backup_service(dummy_service, now)

    dummy_service.set_backuppable(True)
    assert dummy_service.can_be_backed_up()
    assert Backups.is_time_to_backup_service(dummy_service, now)

    Backups.disable_all_autobackup()
    assert not Backups.is_time_to_backup_service(dummy_service, now)
    assert not Backups.is_time_to_backup(now)


def test_autobackup_timing(backups, dummy_service):
    backup_period = 13  # minutes
    now = datetime.now(timezone.utc)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service, now)
    assert Backups.is_time_to_backup(now)

    Backups.back_up(dummy_service)

    now = datetime.now(timezone.utc)
    assert not Backups.is_time_to_backup_service(dummy_service, now)

    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    assert not Backups.is_time_to_backup_service(dummy_service, past)

    future = datetime.now(timezone.utc) + timedelta(minutes=backup_period + 2)
    assert Backups.is_time_to_backup_service(dummy_service, future)


def test_backup_unbackuppable(backups, dummy_service):
    dummy_service.set_backuppable(False)
    assert dummy_service.can_be_backed_up() is False
    with pytest.raises(ValueError):
        Backups.back_up(dummy_service)


def test_failed_autoback_prevents_more_autobackup(backups, dummy_service):
    backup_period = 13  # minutes
    now = datetime.now(timezone.utc)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service, now)

    # artificially making an errored out backup job
    dummy_service.set_backuppable(False)
    with pytest.raises(ValueError):
        Backups.back_up(dummy_service)
    dummy_service.set_backuppable(True)

    assert Backups.get_last_backed_up(dummy_service) is None
    assert Backups.get_last_backup_error_time(dummy_service) is not None

    assert Backups.is_time_to_backup_service(dummy_service, now) is False


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
def test_provider_storage(backups_backblaze):
    provider = Backups.provider()

    assert provider is not None

    assert isinstance(provider, Backblaze)
    assert provider.login == "ID"
    assert provider.key == "KEY"

    Storage.store_provider(provider)
    restored_provider = Backups._load_provider_redis()
    assert isinstance(restored_provider, Backblaze)
    assert restored_provider.login == "ID"
    assert restored_provider.key == "KEY"


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
