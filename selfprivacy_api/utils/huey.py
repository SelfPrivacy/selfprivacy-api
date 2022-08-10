"""MiniHuey singleton."""
from huey import SqliteHuey

HUEY_DATABASE = "/etc/nixos/userdata/tasks.db"

# Singleton instance containing the huey database.
class Huey:
    """Huey singleton."""

    __instance = None

    def __new__(cls):
        """Create a new instance of the huey singleton."""
        if Huey.__instance is None:
            Huey.__instance = SqliteHuey(HUEY_DATABASE)
        return Huey.__instance
