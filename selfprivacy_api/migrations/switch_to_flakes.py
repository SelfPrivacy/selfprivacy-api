from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.services.flake_service_manager import (
    DEFAULT_NIXOS_CONFIG_URL,
    FlakeServiceManager,
    get_sp_module_url,
    is_sp_module_url,
    set_flake_ref,
)


SSO_NIXOS_CONFIG_URL = set_flake_ref(DEFAULT_NIXOS_CONFIG_URL, "sso")


class SwitchToFlakes(Migration):
    """Switch back to the stable branch from the SSO branch."""

    def get_migration_name(self) -> str:
        return "switch_to_flakes"

    def get_migration_description(self) -> str:
        return "Switch back to the stable branch from the SSO branch."

    async def is_migration_needed(self) -> bool:
        async with FlakeServiceManager() as manager:
            for service_url in manager.services.values():
                if is_sp_module_url(service_url, SSO_NIXOS_CONFIG_URL):
                    return True
        return False

    async def migrate(self) -> None:
        async with FlakeServiceManager() as manager:
            for service_name, service_url in manager.services.items():
                if is_sp_module_url(service_url, SSO_NIXOS_CONFIG_URL):
                    manager.services[service_name] = get_sp_module_url(
                        DEFAULT_NIXOS_CONFIG_URL, service_name
                    )
