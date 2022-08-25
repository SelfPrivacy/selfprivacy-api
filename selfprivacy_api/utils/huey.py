"""MiniHuey singleton."""
import os
from huey import SqliteHuey

HUEY_DATABASE = "/etc/nixos/userdata/tasks.db"

# Singleton instance containing the huey database.

test_mode = os.environ.get("TEST_MODE")

huey = SqliteHuey(
    HUEY_DATABASE,
    immediate=test_mode == "true",
)
