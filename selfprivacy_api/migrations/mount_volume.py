import os
import subprocess

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.block_devices import BlockDevices


class MountVolume(Migration):
    """Mount volume."""

    def get_migration_name(self):
        return "mount_volume"

    def get_migration_description(self):
        return "Mount volume if it is not mounted."

    def is_migration_needed(self):
        try:
            with ReadUserData() as userdata:
                return "volumes" not in userdata
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Get info about existing volumes
        # Write info about volumes to userdata.json
        try:
            volumes = BlockDevices().get_block_devices()
            # If there is an unmounted volume sdb,
            # Write it to userdata.json
            is_there_a_volume = False
            for volume in volumes:
                if volume.name == "sdb":
                    is_there_a_volume = True
                    break
            with WriteUserData() as userdata:
                userdata["volumes"] = []
                if is_there_a_volume:
                    userdata["volumes"].append(
                        {
                            "device": "/dev/sdb",
                            "mountPoint": "/volumes/sdb",
                            "fsType": "ext4",
                        }
                    )
            print("Done")
        except Exception as e:
            print(e)
            print("Error mounting volume")
