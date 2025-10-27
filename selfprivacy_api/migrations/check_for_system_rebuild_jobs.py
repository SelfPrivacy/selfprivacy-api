from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.jobs import JobStatus, Jobs


class CheckForSystemRebuildJobs(Migration):
    """Check if there are unfinished system rebuild jobs and finish them"""

    def get_migration_name(self) -> str:
        return "check_for_system_rebuild_jobs"

    def get_migration_description(self) -> str:
        return "Check if there are unfinished system rebuild jobs and finish them"

    async def is_migration_needed(self) -> bool:
        # Check if there are any unfinished system rebuild jobs
        for job in Jobs.get_jobs():
            if (
                job.type_id
                in [
                    "system.nixos.rebuild",
                    "system.nixos.upgrade",
                ]
            ) and job.status in [
                JobStatus.CREATED,
                JobStatus.RUNNING,
            ]:
                return True
        return False

    async def migrate(self) -> None:
        # As the API is restarted, we assume that the jobs are finished
        for job in Jobs.get_jobs():
            if (
                job.type_id
                in [
                    "system.nixos.rebuild",
                    "system.nixos.upgrade",
                ]
            ) and job.status in [
                JobStatus.CREATED,
                JobStatus.RUNNING,
            ]:
                Jobs.update(
                    job=job,
                    status=JobStatus.FINISHED,
                    result="System rebuilt.",
                    progress=100,
                )
