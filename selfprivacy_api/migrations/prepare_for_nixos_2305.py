import os
import subprocess

from selfprivacy_api.migrations.migration import Migration


class MigrateToSelfprivacyChannelFrom2211(Migration):
    """Migrate to selfprivacy Nix channel.
    For some reason NixOS 22.11 servers initialized with the nixos channel instead of selfprivacy.
    This stops us from upgrading to NixOS 23.05
    """

    def get_migration_name(self):
        return "migrate_to_selfprivacy_channel_from_2211"

    def get_migration_description(self):
        return "Migrate to selfprivacy Nix channel from NixOS 22.11."

    def is_migration_needed(self):
        try:
            output = subprocess.check_output(
                ["nix-channel", "--list"], start_new_session=True
            )
            output = output.decode("utf-8")
            first_line = output.split("\n", maxsplit=1)[0]
            return first_line.startswith("nixos") and (
                first_line.endswith("nixos-22.11")
            )
        except subprocess.CalledProcessError:
            return False

    def migrate(self):
        # Change the channel and update them.
        # Also, go to /etc/nixos directory and make a git pull
        current_working_directory = os.getcwd()
        try:
            print("Changing channel")
            os.chdir("/etc/nixos")
            subprocess.check_output(
                [
                    "nix-channel",
                    "--add",
                    "https://channel.selfprivacy.org/nixos-selfpricacy",
                    "nixos",
                ]
            )
            subprocess.check_output(["nix-channel", "--update"])
            nixos_config_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], start_new_session=True
            )
            if nixos_config_branch.decode("utf-8").strip() == "api-redis":
                print("Also changing nixos-config branch from api-redis to master")
                subprocess.check_output(["git", "checkout", "master"])
            subprocess.check_output(["git", "pull"])
            os.chdir(current_working_directory)
        except subprocess.CalledProcessError:
            os.chdir(current_working_directory)
            print("Error")
