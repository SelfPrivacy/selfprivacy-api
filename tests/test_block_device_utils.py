#!/usr/bin/env python3
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import json
import subprocess
import pytest

from selfprivacy_api.utils.block_devices import (
    BlockDevice,
    BlockDevices,
    get_block_device,
    resize_block_device,
)
from tests.common import read_json

SINGLE_LSBLK_OUTPUT = b"""
{
   "blockdevices": [
      {
         "name": "sda1",
         "path": "/dev/sda1",
         "fsavail": "4614107136",
         "fssize": "19814920192",
         "fstype": "ext4",
         "fsused": "14345314304",
         "mountpoints": [
             "/nix/store", "/"
         ],
         "label": null,
         "uuid": "ec80c004-baec-4a2c-851d-0e1807135511",
         "size": 20210236928,
         "model": null,
         "serial": null,
         "type": "part"
      }
   ]
}
"""


@pytest.fixture
def lsblk_singular_mock(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=SINGLE_LSBLK_OUTPUT
    )
    return mock


@pytest.fixture
def failed_check_output_mock(mocker):
    mock = mocker.patch(
        "subprocess.check_output",
        autospec=True,
        side_effect=subprocess.CalledProcessError(
            returncode=1, cmd=["some", "command"]
        ),
    )
    return mock


@pytest.fixture
def only_root_in_userdata(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "only_root.json")
    assert read_json(datadir / "only_root.json")["volumes"][0]["device"] == "/dev/sda1"
    assert (
        read_json(datadir / "only_root.json")["volumes"][0]["mountPoint"]
        == "/volumes/sda1"
    )
    assert read_json(datadir / "only_root.json")["volumes"][0]["fsType"] == "ext4"
    return datadir


@pytest.fixture
def no_devices_in_userdata(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_devices.json")
    assert read_json(datadir / "no_devices.json")["volumes"] == []
    return datadir


@pytest.fixture
def undefined_devices_in_userdata(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "volumes" not in read_json(datadir / "undefined.json")
    return datadir


def test_create_block_device_object(lsblk_singular_mock, authorized_client):
    output = get_block_device("sda1")
    assert lsblk_singular_mock.call_count == 1
    assert lsblk_singular_mock.call_args[0][0] == [
        "lsblk",
        "-J",
        "-b",
        "-o",
        "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINTS,LABEL,UUID,SIZE,MODEL,SERIAL,TYPE",
        "/dev/sda1",
    ]
    assert output == json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0]


def test_resize_block_device(lsblk_singular_mock, authorized_client):
    result = resize_block_device("sdb")
    assert result is True
    assert lsblk_singular_mock.call_count == 1
    assert lsblk_singular_mock.call_args[0][0] == [
        "resize2fs",
        "sdb",
    ]


def test_resize_block_device_failed(failed_check_output_mock, authorized_client):
    result = resize_block_device("sdb")
    assert result is False
    assert failed_check_output_mock.call_count == 1
    assert failed_check_output_mock.call_args[0][0] == [
        "resize2fs",
        "sdb",
    ]


VOLUME_LSBLK_OUTPUT = b"""
{
   "blockdevices": [
      {
         "name": "sdb",
         "path": "/dev/sdb",
         "fsavail": "11888545792",
         "fssize": "12573614080",
         "fstype": "ext4",
         "fsused": "24047616",
         "mountpoints": [
             "/volumes/sdb"
         ],
         "label": null,
         "uuid": "fa9d0026-ee23-4047-b8b1-297ae16fa751",
         "size": 12884901888,
         "model": "Volume",
         "serial": "21378102",
         "type": "disk"
      }
   ]
}
"""


def test_create_block_device(lsblk_singular_mock, authorized_client):
    block_device = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])

    assert block_device.name == "sdb"
    assert block_device.path == "/dev/sdb"
    assert block_device.fsavail == "11888545792"
    assert block_device.fssize == "12573614080"
    assert block_device.fstype == "ext4"
    assert block_device.fsused == "24047616"
    assert block_device.mountpoints == ["/volumes/sdb"]
    assert block_device.label is None
    assert block_device.uuid == "fa9d0026-ee23-4047-b8b1-297ae16fa751"
    assert block_device.size == "12884901888"
    assert block_device.model == "Volume"
    assert block_device.serial == "21378102"
    assert block_device.type == "disk"
    assert block_device.locked is False
    assert str(block_device) == "sdb"
    assert (
        repr(block_device)
        == "<BlockDevice sdb of size 12884901888 mounted at ['/volumes/sdb']>"
    )
    assert hash(block_device) == hash("sdb")


def test_block_devices_equal(lsblk_singular_mock, authorized_client):
    block_device = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])
    block_device2 = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])

    assert block_device == block_device2


@pytest.fixture
def resize_block_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.resize_block_device",
        autospec=True,
        return_value=True,
    )
    return mock


def test_call_resize_from_block_device(
    lsblk_singular_mock, resize_block_mock, authorized_client
):
    block_device = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])
    block_device.resize()
    assert resize_block_mock.call_count == 1
    assert resize_block_mock.call_args[0][0] == "/dev/sdb"
    assert lsblk_singular_mock.call_count == 0


def test_get_stats_from_block_device(lsblk_singular_mock, authorized_client):
    block_device = BlockDevice(json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0])
    stats = block_device.stats()
    assert stats == {
        "name": "sda1",
        "path": "/dev/sda1",
        "fsavail": "4614107136",
        "fssize": "19814920192",
        "fstype": "ext4",
        "fsused": "14345314304",
        "mountpoints": ["/nix/store", "/"],
        "label": None,
        "uuid": "ec80c004-baec-4a2c-851d-0e1807135511",
        "size": "20210236928",
        "model": None,
        "serial": None,
        "type": "part",
    }
    assert lsblk_singular_mock.call_count == 1
    assert lsblk_singular_mock.call_args[0][0] == [
        "lsblk",
        "-J",
        "-b",
        "-o",
        "NAME,PATH,FSAVAIL,FSSIZE,FSTYPE,FSUSED,MOUNTPOINTS,LABEL,UUID,SIZE,MODEL,SERIAL,TYPE",
        "/dev/sda1",
    ]


def test_mount_block_device(
    lsblk_singular_mock, only_root_in_userdata, authorized_client
):
    block_device = BlockDevice(json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0])
    result = block_device.mount()
    assert result is False
    volume = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])
    result = volume.mount()
    assert result is True
    assert (
        read_json(only_root_in_userdata / "only_root.json")["volumes"][1]["device"]
        == "/dev/sdb"
    )
    assert (
        read_json(only_root_in_userdata / "only_root.json")["volumes"][1]["mountPoint"]
        == "/volumes/sdb"
    )
    assert (
        read_json(only_root_in_userdata / "only_root.json")["volumes"][1]["fsType"]
        == "ext4"
    )


def test_mount_block_device_when_undefined(
    lsblk_singular_mock, undefined_devices_in_userdata, authorized_client
):
    block_device = BlockDevice(json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0])
    result = block_device.mount()
    assert result is True
    assert (
        read_json(undefined_devices_in_userdata / "undefined.json")["volumes"][0][
            "device"
        ]
        == "/dev/sda1"
    )
    assert (
        read_json(undefined_devices_in_userdata / "undefined.json")["volumes"][0][
            "mountPoint"
        ]
        == "/volumes/sda1"
    )
    assert (
        read_json(undefined_devices_in_userdata / "undefined.json")["volumes"][0][
            "fsType"
        ]
        == "ext4"
    )


def test_unmount_block_device(
    lsblk_singular_mock, only_root_in_userdata, authorized_client
):
    block_device = BlockDevice(json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0])
    result = block_device.unmount()
    assert result is True
    volume = BlockDevice(json.loads(VOLUME_LSBLK_OUTPUT)["blockdevices"][0])
    result = volume.unmount()
    assert result is False
    assert len(read_json(only_root_in_userdata / "only_root.json")["volumes"]) == 0


def test_unmount_block_device_when_undefined(
    lsblk_singular_mock, undefined_devices_in_userdata, authorized_client
):
    block_device = BlockDevice(json.loads(SINGLE_LSBLK_OUTPUT)["blockdevices"][0])
    result = block_device.unmount()
    assert result is False
    assert (
        len(read_json(undefined_devices_in_userdata / "undefined.json")["volumes"]) == 0
    )


FULL_LSBLK_OUTPUT = b"""
{
   "blockdevices": [
      {
         "name": "sda",
         "path": "/dev/sda",
         "fsavail": null,
         "fssize": null,
         "fstype": null,
         "fsused": null,
         "mountpoints": [
             null
         ],
         "label": null,
         "uuid": null,
         "size": 20480786432,
         "model": "QEMU HARDDISK",
         "serial": "drive-scsi0-0-0-0",
         "type": "disk",
         "children": [
            {
               "name": "sda1",
               "path": "/dev/sda1",
               "fsavail": "4605702144",
               "fssize": "19814920192",
               "fstype": "ext4",
               "fsused": "14353719296",
               "mountpoints": [
                   "/nix/store", "/"
               ],
               "label": null,
               "uuid": "ec80c004-baec-4a2c-851d-0e1807135511",
               "size": 20210236928,
               "model": null,
               "serial": null,
               "type": "part"
            },{
               "name": "sda14",
               "path": "/dev/sda14",
               "fsavail": null,
               "fssize": null,
               "fstype": null,
               "fsused": null,
               "mountpoints": [
                   null
               ],
               "label": null,
               "uuid": null,
               "size": 1048576,
               "model": null,
               "serial": null,
               "type": "part"
            },{
               "name": "sda15",
               "path": "/dev/sda15",
               "fsavail": null,
               "fssize": null,
               "fstype": "vfat",
               "fsused": null,
               "mountpoints": [
                   null
               ],
               "label": null,
               "uuid": "6B29-5BA7",
               "size": 268435456,
               "model": null,
               "serial": null,
               "type": "part"
            }
         ]
      },{
         "name": "sdb",
         "path": "/dev/sdb",
         "fsavail": "11888545792",
         "fssize": "12573614080",
         "fstype": "ext4",
         "fsused": "24047616",
         "mountpoints": [
             "/volumes/sdb"
         ],
         "label": null,
         "uuid": "fa9d0026-ee23-4047-b8b1-297ae16fa751",
         "size": 12884901888,
         "model": "Volume",
         "serial": "21378102",
         "type": "disk"
      },{
         "name": "sr0",
         "path": "/dev/sr0",
         "fsavail": null,
         "fssize": null,
         "fstype": null,
         "fsused": null,
         "mountpoints": [
             null
         ],
         "label": null,
         "uuid": null,
         "size": 1073741312,
         "model": "QEMU DVD-ROM",
         "serial": "QM00003",
         "type": "rom"
      }
   ]
}
"""


@pytest.fixture
def lsblk_full_mock(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=FULL_LSBLK_OUTPUT
    )
    BlockDevices().update()
    return mock


def test_get_block_devices(lsblk_full_mock, authorized_client):
    block_devices = BlockDevices().get_block_devices()
    assert len(block_devices) == 2
    devices_by_name = {device.name: device for device in block_devices}
    sda1 = devices_by_name["sda1"]
    sdb = devices_by_name["sdb"]

    assert sda1.name == "sda1"
    assert sda1.path == "/dev/sda1"
    assert sda1.fsavail == "4605702144"
    assert sda1.fssize == "19814920192"
    assert sda1.fstype == "ext4"
    assert sda1.fsused == "14353719296"
    assert sda1.mountpoints == ["/nix/store", "/"]
    assert sda1.label is None
    assert sda1.uuid == "ec80c004-baec-4a2c-851d-0e1807135511"
    assert sda1.size == "20210236928"
    assert sda1.model is None
    assert sda1.serial is None
    assert sda1.type == "part"

    assert sdb.name == "sdb"
    assert sdb.path == "/dev/sdb"
    assert sdb.fsavail == "11888545792"
    assert sdb.fssize == "12573614080"
    assert sdb.fstype == "ext4"
    assert sdb.fsused == "24047616"
    assert sdb.mountpoints == ["/volumes/sdb"]
    assert sdb.label is None
    assert sdb.uuid == "fa9d0026-ee23-4047-b8b1-297ae16fa751"
    assert sdb.size == "12884901888"
    assert sdb.model == "Volume"
    assert sdb.serial == "21378102"
    assert sdb.type == "disk"


def test_get_block_device(lsblk_full_mock, authorized_client):
    block_device = BlockDevices().get_block_device("sda1")
    assert block_device is not None
    assert block_device.name == "sda1"
    assert block_device.path == "/dev/sda1"
    assert block_device.fsavail == "4605702144"
    assert block_device.fssize == "19814920192"
    assert block_device.fstype == "ext4"
    assert block_device.fsused == "14353719296"
    assert block_device.mountpoints == ["/nix/store", "/"]
    assert block_device.label is None
    assert block_device.uuid == "ec80c004-baec-4a2c-851d-0e1807135511"
    assert block_device.size == "20210236928"
    assert block_device.model is None
    assert block_device.serial is None
    assert block_device.type == "part"


def test_get_block_device_canonical(lsblk_full_mock, authorized_client):
    block_device = BlockDevices().get_block_device_by_canonical_name("sda1")
    assert block_device is not None
    assert block_device.name == "sda1"
    assert block_device.path == "/dev/sda1"
    assert block_device.fsavail == "4605702144"
    assert block_device.fssize == "19814920192"
    assert block_device.fstype == "ext4"
    assert block_device.fsused == "14353719296"
    assert block_device.mountpoints == ["/nix/store", "/"]
    assert block_device.label is None
    assert block_device.uuid == "ec80c004-baec-4a2c-851d-0e1807135511"
    assert block_device.size == "20210236928"
    assert block_device.model is None
    assert block_device.serial is None
    assert block_device.type == "part"


def test_get_nonexistent_block_device(lsblk_full_mock, authorized_client):
    block_device = BlockDevices().get_block_device("sda2")
    assert block_device is None


def test_get_block_devices_by_mountpoint(lsblk_full_mock, authorized_client):
    block_devices = BlockDevices().get_block_devices_by_mountpoint("/nix/store")
    assert len(block_devices) == 1
    assert block_devices[0].name == "sda1"
    assert block_devices[0].path == "/dev/sda1"
    assert block_devices[0].fsavail == "4605702144"
    assert block_devices[0].fssize == "19814920192"
    assert block_devices[0].fstype == "ext4"
    assert block_devices[0].fsused == "14353719296"
    assert block_devices[0].mountpoints == ["/nix/store", "/"]
    assert block_devices[0].label is None
    assert block_devices[0].uuid == "ec80c004-baec-4a2c-851d-0e1807135511"
    assert block_devices[0].size == "20210236928"
    assert block_devices[0].model is None
    assert block_devices[0].serial is None
    assert block_devices[0].type == "part"


def test_get_block_devices_by_mountpoint_no_match(lsblk_full_mock, authorized_client):
    block_devices = BlockDevices().get_block_devices_by_mountpoint("/foo")
    assert len(block_devices) == 0


def test_get_root_block_device(lsblk_full_mock, authorized_client):
    block_device = BlockDevices().get_root_block_device()
    assert block_device is not None
    assert block_device.name == "sda1"
    assert block_device.path == "/dev/sda1"
    assert block_device.fsavail == "4605702144"
    assert block_device.fssize == "19814920192"
    assert block_device.fstype == "ext4"
    assert block_device.fsused == "14353719296"
    assert block_device.mountpoints == ["/nix/store", "/"]
    assert block_device.label is None
    assert block_device.uuid == "ec80c004-baec-4a2c-851d-0e1807135511"
    assert block_device.size == "20210236928"
    assert block_device.model is None
    assert block_device.serial is None
    assert block_device.type == "part"


# Unassuming sanity check, yes this did fail
def test_get_real_devices():
    block_devices = BlockDevices().get_block_devices()

    assert block_devices is not None
    assert len(block_devices) > 0


# Unassuming sanity check
def test_get_real_root_device():
    devices = BlockDevices().get_block_devices()
    try:
        block_device = BlockDevices().get_root_block_device()
    except Exception as e:
        raise Exception("cannot get root device:", e, "devices found:", devices)
    assert block_device is not None
    assert block_device.name is not None
    assert block_device.name != ""


def test_get_real_root_device_raw(authorized_client):
    block_device = BlockDevices().get_root_block_device()
    assert block_device is not None
    assert block_device.name is not None
    assert block_device.name != ""
