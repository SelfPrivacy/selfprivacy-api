import json
import os
import subprocess
import tempfile
import tarfile
import shutil
import time
import urllib.request
from selfprivacy_api.jobs import JobStatus, Jobs
import selfprivacy_api.actions.system as system_actions

from selfprivacy_api.migrations.migration import Migration


class MigrateToFlakes(Migration):
    """Migrate to selfprivacy Nix channel.
    For some reason NixOS 22.11 servers initialized with the nixos channel instead of selfprivacy.
    This stops us from upgrading to NixOS 23.05
    """

    def get_migration_name(self):
        return "migrate_to_flakes"

    def get_migration_description(self):
        return "Migrate to selfprivacy Nix flakes."

    def is_migration_needed(self):
        # Check if there is at least 5 GiB of free space in the root partition
        # This is needed to download the new NixOS configuration
        statvfs = os.statvfs("/")
        free_space = statvfs.f_frsize * statvfs.f_bavail
        if free_space < 5 * 1024 * 1024 * 1024:
            print("===================================")
            print("NOT ENOUGH FREE SPACE FOR MIGRATION")
            print("===================================")
            Jobs.add(
                name="NixOS upgrade to 23.11",
                type_id="migrations.migrate_to_flakes",
                status=JobStatus.ERROR,
                status_text="Not enough free space in the root partition.",
                description="Migration to the modular SelfPrivacy system",
            )
            return False

        return True

    def migrate(self):
        # Change the channel and update them.
        current_working_directory = os.getcwd()
        try:
            print("===========================")
            print("STARTING MIGRATION TO 23.11")
            print("===========================")
            os.chdir("/")

            print("Disabling automatic upgrades to prevent conflicts.")
            subprocess.check_output(
                [
                    "systemctl",
                    "stop",
                    "nixos-upgrade.service",
                    "nixos-upgrade.timer",
                ]
            )
            print("Disabled automatic upgrades.")

            print("Reading the userdata file.")
            userdata_file = open(
                "/etc/nixos/userdata/userdata.json", "r", encoding="utf-8"
            )
            userdata: dict = json.load(userdata_file)
            userdata_file.close()
            print("Read file. Validating contents...")
            assert userdata["dns"]["provider"] is not None
            assert userdata["dns"]["apiKey"] is not None
            assert userdata["useBinds"] is True
            assert userdata["username"] is not None
            assert userdata["username"] != ""
            print("Userdata file is probably fine.")

            print(
                "Moving old NixOS configuration from /etc/nixos to /etc/nixos.pre-flakes"
            )
            subprocess.check_output(
                [
                    "mv",
                    "-v",
                    "/etc/nixos",
                    "/etc/nixos.pre-flakes",
                ]
            )
            assert os.path.exists("/etc/nixos.pre-flakes/userdata/userdata.json")
            print("Moved")

            print("Downloading the template of the new NixOS configuration")

            archive_url = "https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-template/archive/master.tar.gz"
            temp_dir = tempfile.mkdtemp()

            try:
                archive_path = os.path.join(temp_dir, "archive.tar.gz")
                urllib.request.urlretrieve(archive_url, archive_path)

                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=temp_dir)
                    extracted_folder = os.path.join(
                        temp_dir, "selfprivacy-nixos-template"
                    )
                    shutil.copytree(extracted_folder, "/etc/nixos")

            finally:
                shutil.rmtree(temp_dir)
            print("Downloaded")

            print("Copying hardware-configuration.nix")
            hardware_config_path = "/etc/nixos.pre-flakes/hardware-configuration.nix"
            new_hardware_config_path = "/etc/nixos/hardware-configuration.nix"

            with open(hardware_config_path, "r") as hardware_config_file:
                hardware_config_lines = hardware_config_file.readlines()

            # Check if the file contains the line with "./networking.nix" substring
            hardware_config_lines = [
                line for line in hardware_config_lines if "./networking.nix" not in line
            ]

            with open(new_hardware_config_path, "w") as new_hardware_config_file:
                new_hardware_config_file.writelines(hardware_config_lines)
            print("Copied")

            print("Checking if /etc/nixos.pre-flakes/networking.nix exists")
            if os.path.exists("/etc/nixos.pre-flakes/networking.nix"):
                print("Transforming networking.nix to /etc/nixos/deployment.nix")
                deployment_contents = '{ lib, ... }: {\n  system.stateVersion = lib.mkDefault "23.11";\n  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";\n'
                with open(
                    "/etc/nixos.pre-flakes/networking.nix", "r"
                ) as networking_file:
                    networking_contents = networking_file.read().splitlines(True)[1:]
                deployment_contents += "\n" + "".join(networking_contents)
                with open("/etc/nixos/deployment.nix", "w") as file:
                    file.write(deployment_contents)
            else:
                print("Generating /etc/nixos/deployment.nix")
                deployment_contents = '{ lib, ... }: {\n  system.stateVersion = lib.mkDefault "23.11";\n  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";\n}'
                with open("/etc/nixos/deployment.nix", "w") as file:
                    file.write(deployment_contents)

            print("Generated.")

            print("Generating the new userdata file.")
            new_userdata = {
                "dns": {
                    "provider": userdata.get("dns", {}).get("provider", "CLOUDFLARE"),
                    "useStagingACME": False,
                },
                "server": {
                    "provider": userdata.get("server", {}).get("provider", "HETZNER")
                },
                "domain": userdata.get("domain"),
                "hashedMasterPassword": userdata.get("hashedMasterPassword"),
                "hostname": userdata.get("hostname"),
                "timezone": userdata.get("timezone", "Etc/UTC"),
                "username": userdata.get("username"),
                "useBinds": True,
                "sshKeys": userdata.get("sshKeys", []),
                "users": userdata.get("users", []),
                "autoUpgrade": {
                    "enable": userdata.get("autoUpgrade", {}).get("enable", True),
                    "allowReboot": userdata.get("autoUpgrade", {}).get(
                        "allowReboot", False
                    ),
                },
                "modules": {
                    "bitwarden": {
                        "enable": userdata.get("bitwarden", {}).get("enable", False),
                        "location": userdata.get("bitwarden", {}).get(
                            "location", "sda1"
                        ),
                    },
                    "gitea": {
                        "enable": userdata.get("gitea", {}).get("enable", False),
                        "location": userdata.get("gitea", {}).get("location", "sda1"),
                    },
                    "jitsi-meet": {
                        "enable": userdata.get("jitsi", {}).get("enable", False),
                    },
                    "nextcloud": {
                        "enable": userdata.get("nextcloud", {}).get("enable", True),
                        "location": userdata.get("nextcloud", {}).get(
                            "location", "sda1"
                        ),
                    },
                    "ocserv": {
                        "enable": userdata.get("ocserv", {}).get("enable", False),
                    },
                    "pleroma": {
                        "enable": userdata.get("pleroma", {}).get("enable", False),
                        "location": userdata.get("pleroma", {}).get("location", "sda1"),
                    },
                    "simple-nixos-mailserver": {
                        "enable": True,
                        "location": userdata.get("email", {}).get("location", "sda1"),
                    },
                },
                "volumes": userdata.get("volumes", []),
                "ssh": {"rootKeys": userdata.get("ssh", {}).get("rootKeys", [])},
                "stateVersion": "23.11",
            }
            with open("/etc/nixos/userdata.json", "w") as file:
                json.dump(new_userdata, file, indent=4)
            print("New userdata.json generated.")

            print("Generating /etc/selfprivacy/secrets.json")
            subprocess.check_output(
                [
                    "mkdir",
                    "-p",
                    "/etc/selfprivacy",
                ]
            )
            secrets_contents = {
                "databasePassword": userdata.get("databasePassword"),
                "dns": {"apiKey": userdata.get("dns", {}).get("apiKey", "INVALID")},
                "modules": {
                    "nextcloud": {
                        "adminPassword": userdata.get("nextcloud", {}).get(
                            "adminPassword", "INVALID"
                        ),
                        "databasePassword": userdata.get("nextcloud", {}).get(
                            "databasePassword", "INVALID"
                        ),
                    }
                },
            }
            with open("/etc/selfprivacy/secrets.json", "w") as file:
                json.dump(secrets_contents, file, indent=4)
            os.chmod("/etc/selfprivacy/secrets.json", 0o600)
            print("secrets.json generated.")

            print("Building NixOS")
            subprocess.check_output(
                ["nix", "flake", "lock", "/etc/nixos", "--update-input", "sp-modules"]
            )
            subprocess.check_output(
                [
                    "nixos-rebuild",
                    "boot",
                    "--flake",
                    "/etc/nixos#default",
                ]
            )
            print("================================")
            print(
                "NixOS built. Rebooting soon!"
            )
            print("================================")

            Jobs.add(
                name="NixOS upgrade to 23.11",
                type_id="migrations.migrate_to_flakes",
                status=JobStatus.FINISHED,
                status_text="New system built. Check your server API version: if it is 3.0.0 or higher, you've successfully migrated",
                progress=100,
                description="Migration to the modular SelfPrivacy system",
            )

            time.sleep(5)

            system_actions.reboot_system()

        except Exception as error:
            os.chdir(current_working_directory)
            print("Error")
            print(error)
            Jobs.add(
                name="NixOS upgrade to 23.11",
                type_id="migrations.migrate_to_flakes",
                status=JobStatus.ERROR,
                status_text=str(error),
                description="Migration to the modular SelfPrivacy system",
            )
            # Recover the old configuration if the nixos.pre-flakes exists
            if os.path.exists("/etc/nixos.pre-flakes"):
                print("Recovering the old configuration")
                # Move the new configuration to /etc/nixos.new
                subprocess.check_output(
                    [
                        "mv",
                        "-v",
                        "/etc/nixos",
                        "/etc/nixos.failed",
                    ]
                )
                subprocess.check_output(
                    [
                        "mv",
                        "-v",
                        "/etc/nixos.pre-flakes",
                        "/etc/nixos",
                    ]
                )
                print("Recovered the old configuration")
