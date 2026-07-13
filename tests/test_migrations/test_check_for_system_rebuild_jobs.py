# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.jobs import JobStatus, Jobs
from selfprivacy_api.migrations.check_for_system_rebuild_jobs import (
    CheckForSystemRebuildJobs,
)


async def test_finishes_unfinished_system_jobs(jobs):
    created_rebuild = jobs.add(
        type_id="system.nixos.rebuild", name="Rebuild", description=""
    )
    running_upgrade = jobs.add(
        type_id="system.nixos.upgrade",
        name="Upgrade",
        description="",
        status=JobStatus.RUNNING,
    )
    finished_rebuild = jobs.add(
        type_id="system.nixos.rebuild",
        name="Old rebuild",
        description="",
        status=JobStatus.FINISHED,
    )
    running_backup = jobs.add(
        type_id="backups.backup",
        name="Backup",
        description="",
        status=JobStatus.RUNNING,
    )
    migration = CheckForSystemRebuildJobs()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    for job in [created_rebuild, running_upgrade]:
        updated = Jobs.get_job(str(job.uid))
        assert updated is not None
        assert updated.status == JobStatus.FINISHED
        assert updated.result == "System rebuilt."
        assert updated.progress == 100

    untouched_backup = Jobs.get_job(str(running_backup.uid))
    assert untouched_backup is not None
    assert untouched_backup.status == JobStatus.RUNNING

    untouched_finished = Jobs.get_job(str(finished_rebuild.uid))
    assert untouched_finished is not None
    assert untouched_finished.result is None

    assert await migration.is_migration_needed() is False


async def test_not_needed_with_no_jobs(jobs):
    assert await CheckForSystemRebuildJobs().is_migration_needed() is False


async def test_not_needed_when_system_jobs_finished(jobs):
    jobs.add(
        type_id="system.nixos.rebuild",
        name="Rebuild",
        description="",
        status=JobStatus.FINISHED,
    )
    jobs.add(
        type_id="system.nixos.upgrade",
        name="Upgrade",
        description="",
        status=JobStatus.ERROR,
    )

    assert await CheckForSystemRebuildJobs().is_migration_needed() is False
