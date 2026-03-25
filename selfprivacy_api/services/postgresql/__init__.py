"""Class representing Nextcloud service."""

import base64
import subprocess
from typing import List, Optional

from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.postgresql.icon import POSTGRESQL_ICON
from selfprivacy_api.services.service import Service, ServiceStatus
from selfprivacy_api.utils.systemd import (
    get_service_status,
    restart_unit,
    start_unit,
    stop_unit,
    wait_for_unit_state,
)


class PostgreSQL(Service):
    """Class representing PostgreSQL service."""

    @staticmethod
    def get_id() -> str:
        return "monitoring"

    @staticmethod
    def get_display_name() -> str:
        return "PostgreSQL"

    @staticmethod
    def get_description() -> str:
        return "PostgreSQL is used for resource monitoring and alerts."

    @staticmethod
    def get_svg_icon(raw=False) -> str:
        if raw:
            return POSTGRESQL_ICON
        return base64.b64encode(POSTGRESQL_ICON.encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_url() -> Optional[str]:
        """Return service url."""
        return None

    @staticmethod
    def get_subdomain() -> Optional[str]:
        return None

    @staticmethod
    def is_movable() -> bool:
        return False

    @staticmethod
    def is_required() -> bool:
        return True

    @staticmethod
    def is_system_service() -> bool:
        return True

    @staticmethod
    def can_be_backed_up() -> bool:
        return False

    @staticmethod
    def get_backup_description() -> str:
        return "Backups are not available for PostgreSQL."

    @staticmethod
    async def get_status() -> ServiceStatus:
        return await get_service_status("postgresql.service")

    @staticmethod
    async def wait_for_statuses(self, expected_statuses: List[ServiceStatus]):
        await wait_for_unit_state("postgresql.service", expected_statuses)

    @staticmethod
    async def stop():
        await stop_unit("postgresql.service")
        subprocess.run(["systemctl", "stop", "postgresql.service"])

    @staticmethod
    async def start():
        await start_unit("postgresql.service")

    @staticmethod
    async def restart():
        await restart_unit("postgresql.service")

    @staticmethod
    def get_owned_folders() -> List[OwnedPath]:
        return [
            OwnedPath(
                path="/var/lib/postgresql",
                owner="postgresql",
                group="postgresql",
            ),
        ]
