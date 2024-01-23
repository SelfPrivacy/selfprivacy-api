"""MiniHuey singleton."""
import os
from huey import SqliteHuey

HUEY_DATABASE = "/etc/selfprivacy/tasks.db"

# Singleton instance containing the huey database.

test_mode = os.environ.get("TEST_MODE")

huey = SqliteHuey(
    "selfprivacy-api",
    filename=HUEY_DATABASE if not test_mode else None,
    immediate=test_mode == "true",
    utc=True,
)
