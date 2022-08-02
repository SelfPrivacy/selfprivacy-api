"""Function to perform migration of app data to binds."""
import subprocess
import psutil
import pathlib
import shutil
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.utils import WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices

class BindMigrationConfig:
    """Config for bind migration.
    For each service provide block device name.
    """
    email_block_device: str
    bitwarden_block_device: str
    gitea_block_device: str
    nextcloud_block_device: str
    pleroma_block_device: str


def migrate_to_binds(config: BindMigrationConfig):
    """Migrate app data to binds."""

    # Get block devices.
    block_devices = BlockDevices().get_block_devices()
    block_device_names = [ device.name for device in block_devices ]

    # Get all unique required block devices
    required_block_devices = []
    for block_device_name in config.__dict__.values():
        if block_device_name not in required_block_devices:
            required_block_devices.append(block_device_name)

    # Check if all block devices from config are present.
    for block_device_name in required_block_devices:
        if block_device_name not in block_device_names:
            raise Exception(f"Block device {block_device_name} is not present.")

    # Make sure all required block devices are mounted.
    # sda1 is the root partition and is always mounted.
    for block_device_name in required_block_devices:
        if block_device_name == "sda1":
            continue
        block_device = BlockDevices().get_block_device(block_device_name)
        if block_device is None:
            raise Exception(f"Block device {block_device_name} is not present.")
        if f"/volumes/{block_device_name}" not in block_device.mountpoints:
            raise Exception(f"Block device {block_device_name} is not mounted.")

    # Activate binds in userdata
    with WriteUserData() as user_data:
        if "email" not in user_data:
            user_data["email"] = {}
        user_data["email"]["block_device"] = config.email_block_device
        if "bitwarden" not in user_data:
            user_data["bitwarden"] = {}
        user_data["bitwarden"]["block_device"] = config.bitwarden_block_device
        if "gitea" not in user_data:
            user_data["gitea"] = {}
        user_data["gitea"]["block_device"] = config.gitea_block_device
        if "nextcloud" not in user_data:
            user_data["nextcloud"] = {}
        user_data["nextcloud"]["block_device"] = config.nextcloud_block_device
        if "pleroma" not in user_data:
            user_data["pleroma"] = {}
        user_data["pleroma"]["block_device"] = config.pleroma_block_device

        user_data["useBinds"] = True

    # Make sure /volumes/sda1 exists.
    pathlib.Path("/volumes/sda1").mkdir(parents=True, exist_ok=True)

    # Perform migration of Nextcloud.
    # Data is moved from /var/lib/nextcloud to /volumes/<block_device_name>/nextcloud.
    # /var/lib/nextcloud is removed and /volumes/<block_device_name>/nextcloud is mounted as bind mount.

    # Turn off Nextcloud
    Nextcloud().stop()

    # Move data from /var/lib/nextcloud to /volumes/<block_device_name>/nextcloud.
    # /var/lib/nextcloud is removed and /volumes/<block_device_name>/nextcloud is mounted as bind mount.
    nextcloud_data_path = pathlib.Path("/var/lib/nextcloud")
    nextcloud_bind_path = pathlib.Path(f"/volumes/{config.nextcloud_block_device}/nextcloud")
    if nextcloud_data_path.exists():
        shutil.move(str(nextcloud_data_path), str(nextcloud_bind_path))
    else:
        raise Exception("Nextcloud data path does not exist.")

    # Make sure folder /var/lib/nextcloud exists.
    nextcloud_data_path.mkdir(mode=0o750, parents=True, exist_ok=True)

    # Make sure this folder is owned by user nextcloud and group nextcloud.
    shutil.chown(nextcloud_bind_path, user="nextcloud", group="nextcloud")
    shutil.chown(nextcloud_data_path, user="nextcloud", group="nextcloud")

    # Mount nextcloud bind mount.
    subprocess.run(["mount","--bind", str(nextcloud_bind_path), str(nextcloud_data_path)], check=True)

    # Recursively chown all files in nextcloud bind mount.
    subprocess.run(["chown", "-R", "nextcloud:nextcloud", str(nextcloud_data_path)], check=True)

    # Start Nextcloud
    Nextcloud().start()
