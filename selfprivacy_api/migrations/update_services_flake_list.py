from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.jobs import JobStatus, Jobs

from selfprivacy_api.services.flake_service_manager import FlakeServiceManager

CORRECT_SERVICES_LIST = {
    "bitwarden": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/bitwarden",
    "gitea": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/gitea",
    "jitsi-meet": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/jitsi-meet",
    "nextcloud": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/nextcloud",
    "ocserv": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/ocserv",
    "pleroma": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/pleroma",
    "simple-nixos-mailserver": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/simple-nixos-mailserver",
    "roundcube": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes&dir=sp-modules/roundcube",
}


class UpdateServicesFlakeList(Migration):
    """Check if all required services are in the flake list"""

    def get_migration_name(self):
        return "update_services_flake_list"

    def get_migration_description(self):
        return "Check if all required services are in the flake list"

    def is_migration_needed(self):
        for key, value in manager.services.items():
            if key not in CORRECT_SERVICES_LIST:
                return True

    def migrate(self):
        with FlakeServiceManager:
            for key, value in CORRECT_SERVICES_LIST.items():
                if key not in manager.services:
                    manager.services[key] = value
