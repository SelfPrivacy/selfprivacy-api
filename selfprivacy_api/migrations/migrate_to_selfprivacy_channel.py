import os
import subprocess

from selfprivacy_api.migrations.migration import Migration


class MigrateToSelfprivacyChannel(Migration):
    """Migrate to selfprivacy Nix channel."""
    def get_migration_name(self):
        return "migrate_to_selfprivacy_channel"

    def get_migration_description(self):
        return "Migrate to selfprivacy Nix channel."

    def is_migration_needed(self):
        try:
            print("Checking if migration is needed")
            output = subprocess.check_output(
                ["nix-channel", "--list"], start_new_session=True
            )
            output = output.decode("utf-8")
            print(output)
            first_line = output.split("\n", maxsplit=1)[0]
            print(first_line)
            return first_line.startswith("nixos") and (
                first_line.endswith("nixos-21.11") or first_line.endswith("nixos-21.05")
            )
        except subprocess.CalledProcessError:
            return False
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
            subprocess.check_output(["git", "pull"])
            os.chdir(current_working_directory)
        except subprocess.CalledProcessError:
            os.chdir(current_working_directory)
            print("Error")
