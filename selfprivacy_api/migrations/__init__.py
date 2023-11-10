"""Migrations module.
Migrations module is introduced in v1.1.1 and provides one-shot
migrations which cannot be performed from the NixOS configuration file changes.
These migrations are checked and ran before every start of the API.

You can disable certain migrations if needed by creating an array
at api.skippedMigrations in userdata.json and populating it
with IDs of the migrations to skip.
Adding DISABLE_ALL to that array disables the migrations module entirely.
"""
from selfprivacy_api.migrations.check_for_failed_binds_migration import (
    CheckForFailedBindsMigration,
)
from selfprivacy_api.utils import ReadUserData
from selfprivacy_api.migrations.fix_nixos_config_branch import FixNixosConfigBranch
from selfprivacy_api.migrations.create_tokens_json import CreateTokensJson
from selfprivacy_api.migrations.migrate_to_selfprivacy_channel import (
    MigrateToSelfprivacyChannel,
)
from selfprivacy_api.migrations.mount_volume import MountVolume
from selfprivacy_api.migrations.providers import CreateProviderFields
from selfprivacy_api.migrations.prepare_for_nixos_2211 import (
    MigrateToSelfprivacyChannelFrom2205,
)
from selfprivacy_api.migrations.prepare_for_nixos_2305 import (
    MigrateToSelfprivacyChannelFrom2211,
)
from selfprivacy_api.migrations.redis_tokens import LoadTokensToRedis

migrations = [
    FixNixosConfigBranch(),
    CreateTokensJson(),
    MigrateToSelfprivacyChannel(),
    MountVolume(),
    CheckForFailedBindsMigration(),
    CreateProviderFields(),
    MigrateToSelfprivacyChannelFrom2205(),
    MigrateToSelfprivacyChannelFrom2211(),
    LoadTokensToRedis(),
]


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
            except Exception as err:
                print(f"Error while migrating {migration.get_migration_name()}")
                print(err)
                print("Skipping this migration")
