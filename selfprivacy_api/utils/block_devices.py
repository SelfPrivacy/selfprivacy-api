"""Wrapper for block device functions."""
import subprocess
import json
import typing

from selfprivacy_api.utils import WriteUserData


def get_block_device(device_name):
    """
    Return a block device by name.
    """
    lsblk_output = subprocess.check_output(
        [
            "lsblk",
            "-J",
            "-b",
            "-o",
            "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINT,LABEL,UUID,SIZE, MODEL,SERIAL,TYPE",
            device_name,
        ]
    )
    lsblk_output = lsblk_output.decode("utf-8")
    lsblk_output = json.loads(lsblk_output)
    return lsblk_output["blockdevices"]


def resize_block_device(block_device) -> bool:
    """
    Resize a block device. Return True if successful.
    """
    resize_command = ["resize2fs", block_device]
    resize_process = subprocess.Popen(resize_command, shell=False)
    resize_process.communicate()
    return resize_process.returncode == 0


class BlockDevice:
    """
    A block device.
    """

    def __init__(self, block_device):
        self.name = block_device["name"]
        self.path = block_device["path"]
        self.fsavail = block_device["fsavail"]
        self.fssize = block_device["fssize"]
        self.fstype = block_device["fstype"]
        self.fsused = block_device["fsused"]
        self.mountpoint = block_device["mountpoint"]
        self.label = block_device["label"]
        self.uuid = block_device["uuid"]
        self.size = block_device["size"]
        self.model = block_device["model"]
        self.serial = block_device["serial"]
        self.type = block_device["type"]
        self.locked = False

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<BlockDevice {self.name} of size {self.size} mounted at {self.mountpoint}>"

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def stats(self) -> typing.Dict[str, typing.Any]:
        """
        Update current data and return a dictionary of stats.
        """
        device = get_block_device(self.name)
        self.fsavail = device["fsavail"]
        self.fssize = device["fssize"]
        self.fstype = device["fstype"]
        self.fsused = device["fsused"]
        self.mountpoint = device["mountpoint"]
        self.label = device["label"]
        self.uuid = device["uuid"]
        self.size = device["size"]
        self.model = device["model"]
        self.serial = device["serial"]
        self.type = device["type"]

        return {
            "name": self.name,
            "path": self.path,
            "fsavail": self.fsavail,
            "fssize": self.fssize,
            "fstype": self.fstype,
            "fsused": self.fsused,
            "mountpoint": self.mountpoint,
            "label": self.label,
            "uuid": self.uuid,
            "size": self.size,
            "model": self.model,
            "serial": self.serial,
            "type": self.type,
        }

    def resize(self):
        """
        Resize the block device.
        """
        if not self.locked:
            self.locked = True
            resize_block_device(self.path)
            self.locked = False

    def mount(self) -> bool:
        """
        Mount the block device.
        """
        with WriteUserData() as user_data:
            if "volumes" not in user_data:
                user_data["volumes"] = []
            # Check if the volume is already mounted
            for volume in user_data["volumes"]:
                if volume["device"] == self.path:
                    return False
            user_data["volumes"].append(
                {
                    "device": self.path,
                    "mountPoint": f"/volumes/{self.name}",
                    "fsType": self.fstype,
                }
            )
        return True

    def unmount(self) -> bool:
        """
        Unmount the block device.
        """
        with WriteUserData() as user_data:
            if "volumes" not in user_data:
                user_data["volumes"] = []
            # Check if the volume is already mounted
            for volume in user_data["volumes"]:
                if volume["device"] == self.path:
                    user_data["volumes"].remove(volume)
                    return True
        return False


class BlockDevices:
    """Singleton holding all Block devices"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.block_devices = []
        self.update()

    def update(self) -> None:
        """
        Update the list of block devices.
        """
        devices = []
        lsblk_output = subprocess.check_output(
            [
                "lsblk",
                "-J",
                "-b",
                "-o",
                "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINT,LABEL,UUID,SIZE,MODEL,SERIAL,TYPE",
            ]
        )
        lsblk_output = lsblk_output.decode("utf-8")
        lsblk_output = json.loads(lsblk_output)
        for device in lsblk_output["blockdevices"]:
            # Ignore devices with type "rom"
            if device["type"] == "rom":
                continue
            if device["fstype"] is None:
                if "children" in device:
                    for child in device["children"]:
                        if child["fstype"] == "ext4":
                            device = child
                            break
            devices.append(device)
        # Add new devices and delete non-existent devices
        for device in devices:
            if device["name"] not in [
                block_device.name for block_device in self.block_devices
            ]:
                self.block_devices.append(BlockDevice(device))
        for block_device in self.block_devices:
            if block_device.name not in [device["name"] for device in devices]:
                self.block_devices.remove(block_device)

    def get_block_device(self, name: str) -> typing.Optional[BlockDevice]:
        """
        Return a block device by name.
        """
        for block_device in self.block_devices:
            if block_device.name == name:
                return block_device
        return None

    def get_block_devices(self) -> typing.List[BlockDevice]:
        """
        Return a list of block devices.
        """
        return self.block_devices

    def get_block_devices_by_mountpoint(
        self, mountpoint: str
    ) -> typing.List[BlockDevice]:
        """
        Return a list of block devices with a given mountpoint.
        """
        block_devices = []
        for block_device in self.block_devices:
            if block_device.mountpoint == mountpoint:
                block_devices.append(block_device)
        return block_devices
