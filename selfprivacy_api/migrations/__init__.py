from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.migrations.fix_nixos_config_branch import FixNixosConfigBranch
from selfprivacy_api.migrations.create_tokens_json import CreateTokensJson

migrations = [FixNixosConfigBranch(), CreateTokensJson()]


def run_migrations():
    """
    Go over all migrations. If they are not skipped in userdata file, run them
    if the migration needed.
    """
    with ReadUserData() as data:
        if "api" not in data:
            skipped_migrations = []
        elif "skippedMigrations" not in data["api"]:
            skipped_migrations = []
        else:
            skipped_migrations = data["api"].get("skippedMigrations", [])

    if "DISABLE_ALL" in skipped_migrations:
        return

    for migration in migrations:
        if migration.get_migration_name() not in skipped_migrations:
            try:
                if migration.is_migration_needed():
                    migration.migrate()
            except Exception as e:
                print(f"Error while migrating {migration.get_migration_name()}")
                print(e)
                print("Skipping this migration")
