import os
import subprocess

from selfprivacy_api.migrations.migration import Migration


class FixNixosConfigBranch(Migration):
    def get_migration_name(self):
        return "fix_nixos_config_branch"

    def get_migration_description(self):
        return """Mobile SelfPrivacy app introduced a bug in version 0.4.0.
        New servers were initialized with a rolling-testing nixos config branch.
        This was fixed in app version 0.4.2, but existing servers were not updated.
        This migration fixes this by changing the nixos config branch to master.
        """

    def is_migration_needed(self):
        """Check the current branch of /etc/nixos and return True if it is rolling-testing"""
        current_working_directory = os.getcwd()
        try:
            os.chdir("/etc/nixos")
            nixos_config_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], start_new_session=True
            )
            os.chdir(current_working_directory)
            if nixos_config_branch.decode("utf-8").strip() == "rolling-testing":
                return True
            else:
                return False
        except subprocess.CalledProcessError:
            os.chdir(current_working_directory)
            return False

    def migrate(self):
        """Affected server pulled the config with the --single-branch flag.
        Git config remote.origin.fetch has to be changed, so all branches will be fetched.
        Then, fetch all branches, pull and switch to master branch.
        """
        print("Fixing Nixos config branch")
        current_working_directory = os.getcwd()
        try:
            os.chdir("/etc/nixos")

            subprocess.check_output(
                [
                    "git",
                    "config",
                    "remote.origin.fetch",
                    "+refs/heads/*:refs/remotes/origin/*",
                ]
            )
            subprocess.check_output(["git", "fetch", "--all"])
            subprocess.check_output(["git", "pull"])
            subprocess.check_output(["git", "checkout", "master"])
            os.chdir(current_working_directory)
            print("Done")
        except subprocess.CalledProcessError:
            os.chdir(current_working_directory)
            print("Error")
