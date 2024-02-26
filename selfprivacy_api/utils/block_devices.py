"""A block device API wrapping lsblk"""
from __future__ import annotations
import subprocess
import json
import typing

from pydantic import BaseModel

from selfprivacy_api.utils import WriteUserData
from selfprivacy_api.utils.singleton_metaclass import SingletonMetaclass


def get_block_device(device_name):
    """
    Return a block device by name.
    """
    # TODO: remove the function and related tests: dublicated by singleton
    lsblk_output = subprocess.check_output(
        [
            "lsblk",
            "-J",
            "-b",
            "-o",
            "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINTS,LABEL,UUID,SIZE,MODEL,SERIAL,TYPE",
            f"/dev/{device_name}",
        ]
    )
    lsblk_output = lsblk_output.decode("utf-8")
    lsblk_output = json.loads(lsblk_output)
    return lsblk_output["blockdevices"][0]


def resize_block_device(block_device) -> bool:
    """
    Resize a block device. Return True if successful.
    """
    resize_command = ["resize2fs", block_device]
    try:
        subprocess.check_output(resize_command, shell=False)
    except subprocess.CalledProcessError:
        return False
    return True


class BlockDevice:
    """
    A block device.
    """

    def __init__(self, device_dict: dict):
        self.update_from_dict(device_dict)

    def update_from_dict(self, device_dict: dict):
        self.name = device_dict["name"]
        self.path = device_dict["path"]
        self.fsavail = str(device_dict["fsavail"])
        self.fssize = str(device_dict["fssize"])
        self.fstype = device_dict["fstype"]
        self.fsused = str(device_dict["fsused"])
        self.mountpoints = device_dict["mountpoints"]
        self.label = device_dict["label"]
        self.uuid = device_dict["uuid"]
        self.size = str(device_dict["size"])
        self.model = device_dict["model"]
        self.serial = device_dict["serial"]
        self.type = device_dict["type"]
        self.locked = False

        self.children: typing.List[BlockDevice] = []
        if "children" in device_dict.keys():
            for child in device_dict["children"]:
                self.children.append(BlockDevice(child))

    def all_children(self) -> typing.List[BlockDevice]:
        result = []
        for child in self.children:
            result.extend(child.all_children())
            result.append(child)
        return result

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<BlockDevice {self.name} of size {self.size} mounted at {self.mountpoints}>"

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def is_root(self) -> bool:
        """
        Return True if the block device is the root device.
        """
        return "/" in self.mountpoints

    def stats(self) -> typing.Dict[str, typing.Any]:
        """
        Update current data and return a dictionary of stats.
        """
        device = get_block_device(self.name)
        self.update_from_dict(device)

        return {
            "name": self.name,
            "path": self.path,
            "fsavail": self.fsavail,
            "fssize": self.fssize,
            "fstype": self.fstype,
            "fsused": self.fsused,
            "mountpoints": self.mountpoints,
            "label": self.label,
            "uuid": self.uuid,
            "size": self.size,
            "model": self.model,
            "serial": self.serial,
            "type": self.type,
        }

    def is_usable_partition(self):
        # Ignore devices with type "rom"
        if self.type == "rom":
            return False
        if self.fstype == "ext4":
            return True
        return False

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


class BlockDevices(metaclass=SingletonMetaclass):
    """Singleton holding all Block devices"""

    def __init__(self):
        self.block_devices = []
        self.update()

    def update(self) -> None:
        """
        Update the list of block devices.
        """
        devices = BlockDevices.lsblk_devices()

        children = []
        for device in devices:
            children.extend(device.all_children())
        devices.extend(children)

        valid_devices = [device for device in devices if device.is_usable_partition()]

        self.block_devices = valid_devices

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
            if mountpoint in block_device.mountpoints:
                block_devices.append(block_device)
        return block_devices

    def get_root_block_device(self) -> BlockDevice:
        """
        Return the root block device.
        """
        for block_device in self.block_devices:
            if "/" in block_device.mountpoints:
                return block_device
        raise RuntimeError("No root block device found")

    @staticmethod
    def lsblk_device_dicts() -> typing.List[dict]:
        lsblk_output_bytes = subprocess.check_output(
            [
                "lsblk",
                "-J",
                "-b",
                "-o",
                "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINTS,LABEL,UUID,SIZE,MODEL,SERIAL,TYPE",
            ]
        )
        lsblk_output = lsblk_output_bytes.decode("utf-8")
        return json.loads(lsblk_output)["blockdevices"]

    @staticmethod
    def lsblk_devices() -> typing.List[BlockDevice]:
        devices = []
        for device in BlockDevices.lsblk_device_dicts():
            devices.append(device)

        return [BlockDevice(device) for device in devices]
