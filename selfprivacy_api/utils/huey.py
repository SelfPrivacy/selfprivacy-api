"""MiniHuey singleton."""
from huey import SqliteHuey

HUEY_DATABASE = "/etc/nixos/userdata/tasks.db"

# Singleton instance containing the huey database.

huey = SqliteHuey(HUEY_DATABASE)
