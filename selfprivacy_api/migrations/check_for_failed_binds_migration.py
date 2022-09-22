from selfprivacy_api.jobs import JobStatus, Jobs

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import WriteUserData


class CheckForFailedBindsMigration(Migration):
    """Mount volume."""

    def get_migration_name(self):
        return "check_for_failed_binds_migration"

    def get_migration_description(self):
        return "If binds migration failed, try again."

    def is_migration_needed(self):
        try:
            jobs = Jobs.get_instance().get_jobs()
            # If there is a job with type_id "migrations.migrate_to_binds" and status is not "FINISHED",
            # then migration is needed and job is deleted
            for job in jobs:
                if (
                    job.type_id == "migrations.migrate_to_binds"
                    and job.status != JobStatus.FINISHED
                ):
                    return True
            return False
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Get info about existing volumes
        # Write info about volumes to userdata.json
        try:
            jobs = Jobs.get_instance().get_jobs()
            for job in jobs:
                if (
                    job.type_id == "migrations.migrate_to_binds"
                    and job.status != JobStatus.FINISHED
                ):
                    Jobs.get_instance().remove(job)
            with WriteUserData() as userdata:
                userdata["useBinds"] = False
            print("Done")
        except Exception as e:
            print(e)
            print("Error mounting volume")
