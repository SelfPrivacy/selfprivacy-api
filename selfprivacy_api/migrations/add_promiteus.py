from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager
from selfprivacy_api.utils import ReadUserData, WriteUserData


class AddPrometheus(Migration):
    """Adds the Prometheus if it is not present."""

    def get_migration_name(self) -> str:
        return "add_prometheus"

    def get_migration_description(self) -> str:
        return "Adds the Prometheus if it is not present."

    def is_migration_needed(self) -> bool:
        with FlakeServiceManager() as manager:
            if "prometheus" not in manager.services:
                return True
        with ReadUserData() as data:
            if "prometheus" not in data["modules"]:
                return True
        return False

    def migrate(self) -> None:
        with FlakeServiceManager() as manager:
            if "prometheus" not in manager.services:
                manager.services["prometheus"] = (
                    "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/prometheus"
                )
        with WriteUserData() as data:
            if "prometheus" not in data["modules"]:
                data["modules"]["prometheus"] = {
                    "enable": False,
                    "subdomain": "prometheus",
                }
