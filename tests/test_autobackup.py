import pytest
from copy import copy

from datetime import datetime, timezone, timedelta

from selfprivacy_api.jobs import Jobs
from selfprivacy_api.services import Service, get_all_services

from selfprivacy_api.graphql.common_types.backup import (
    BackupReason,
    AutobackupQuotas,
)

from selfprivacy_api.backup import Backups, Snapshot
from selfprivacy_api.backup.tasks import (
    prune_autobackup_snapshots,
    do_autobackup,
)
from selfprivacy_api.backup.jobs import autobackup_job_type

from tests.test_backup import backups, assert_job_finished
from tests.test_graphql.test_services import only_dummy_service


def backuppable_services() -> list[Service]:
    return [service for service in get_all_services() if service.can_be_backed_up()]


def dummy_snapshot(date: datetime):
    return Snapshot(
        id=str(hash(date)),
        service_name="someservice",
        created_at=date,
        reason=BackupReason.EXPLICIT,
    )


def test_no_default_autobackup(backups, dummy_service):
    now = datetime.now(timezone.utc)
    assert not Backups.is_time_to_backup_service(dummy_service, now)
    assert not Backups.is_time_to_backup(now)


# --------------------- Timing -------------------------


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


def test_autobackup_taskbody(backups, only_dummy_service):
    # We cannot test the timed task itself, but we reduced it
    # to one line, and we test this line here
    dummy_service = only_dummy_service
    now = datetime.now(timezone.utc)
    backup_period = 13  # minutes

    assert Backups.get_all_snapshots() == []
    assert_job_finished(autobackup_job_type(), count=0)

    Backups.set_autobackup_period_minutes(backup_period)
    assert Backups.is_time_to_backup_service(dummy_service, now)
    assert Backups.is_time_to_backup(now)
    assert dummy_service in Backups.services_to_back_up(now)
    assert len(Backups.services_to_back_up(now)) == 1

    do_autobackup()

    snapshots = Backups.get_all_snapshots()
    assert len(snapshots) == 1
    assert snapshots[0].service_name == dummy_service.get_id()
    assert snapshots[0].reason == BackupReason.AUTO

    assert_job_finished(autobackup_job_type(), count=1)


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


# --------------------- What to autobackup and what not to --------------------


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


# --------------------- Quotas and Pruning -------------------------


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


def test_quotas_exceeded_with_too_many_autobackups(backups, dummy_service):
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
