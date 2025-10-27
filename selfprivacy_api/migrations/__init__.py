"""Migrations module.
Migrations module is introduced in v1.1.1 and provides one-shot
migrations which cannot be performed from the NixOS configuration file changes.
These migrations are checked and ran before every start of the API.

You can disable certain migrations if needed by creating an array
at api.skippedMigrations in userdata.json and populating it
with IDs of the migrations to skip.
Adding DISABLE_ALL to that array disables the migrations module entirely.
"""

import logging
import traceback

from selfprivacy_api.utils import ReadUserData, UserDataFiles
from selfprivacy_api.migrations.write_token_to_redis import WriteTokenToRedis
from selfprivacy_api.migrations.check_for_system_rebuild_jobs import (
    CheckForSystemRebuildJobs,
)
from selfprivacy_api.migrations.add_roundcube import AddRoundcube
from selfprivacy_api.migrations.add_monitoring import AddMonitoring
from selfprivacy_api.migrations.migrate_users_from_json import MigrateUsersFromJson
from selfprivacy_api.migrations.add_postgres_location import AddPostgresLocation
from selfprivacy_api.migrations.replace_blockdevices_to_uuid import (
    ReplaceBlockDevicesToUUID,
)

from selfprivacy_api.migrations.switch_to_flakes import SwitchToFlakes

logger = logging.getLogger(__name__)

migrations = [
    WriteTokenToRedis(),
    CheckForSystemRebuildJobs(),
    AddMonitoring(),
    AddRoundcube(),
    MigrateUsersFromJson(),
    AddPostgresLocation(),
    SwitchToFlakes(),
    ReplaceBlockDevicesToUUID(),
]


async def run_migrations():
    """
    Go over all migrations. If they are not skipped in userdata file, run them
    if the migration needed.
    """
    with ReadUserData(UserDataFiles.SECRETS) as data:
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
                if await migration.is_migration_needed():
                    await migration.migrate()
            except Exception:
                logging.error(f"Error while migrating {migration.get_migration_name()}")
                logging.error(traceback.format_exc())
                logging.error("Skipping this migration")
