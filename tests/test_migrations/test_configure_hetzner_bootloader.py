import pytest

from selfprivacy_api.migrations.configure_hetzner_bootloader import (
    EFI_FIRMWARE_PATH,
    is_efi_booted,
    ConfigureHetznerBootloader,
    get_system_disk_by_id,
)
from selfprivacy_api.utils import ReadUserData, WriteUserData


def test_is_efi_booted(mocker):
    isdir = mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.os.path.isdir",
        return_value=True,
    )

    assert is_efi_booted() is True
    isdir.assert_called_once_with(EFI_FIRMWARE_PATH)


# generic_userdata uses HETZNER as provider
async def test_needed_when_bootloader_is_missing(generic_userdata, mocker):
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.is_efi_booted",
        return_value=False,
    )

    assert await ConfigureHetznerBootloader().is_migration_needed() is True


async def test_not_needed_for_digitalocean(generic_userdata):
    with WriteUserData() as data:
        data["server"]["provider"] = "DIGITALOCEAN"

    assert await ConfigureHetznerBootloader().is_migration_needed() is False


async def test_not_needed_when_efi_booted(generic_userdata, mocker):
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.is_efi_booted",
        return_value=True,
    )

    assert await ConfigureHetznerBootloader().is_migration_needed() is False


async def test_not_needed_when_bootloader_exists(generic_userdata):
    with WriteUserData() as data:
        data["server"]["bootloader"] = {
            "type": "grub-mbr",
            "device": "/dev/disk/by-id/wwn-x",
        }

    assert await ConfigureHetznerBootloader().is_migration_needed() is False


async def test_migrate_records_grub_mbr_target(generic_userdata, mocker):
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.get_system_disk_by_id",
        return_value="/dev/disk/by-id/wwn-0x123",
    )

    await ConfigureHetznerBootloader().migrate()

    with ReadUserData() as data:
        assert data["server"]["bootloader"] == {
            "type": "grub-mbr",
            "device": "/dev/disk/by-id/wwn-0x123",
        }


def test_system_disk_by_id_fails_without_parent_disk(mocker):
    root_partition = mocker.Mock(path="/dev/sda1")
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.BlockDevices",
        return_value=mocker.Mock(get_root_block_device=lambda: root_partition),
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.subprocess.check_output",
        return_value="\n",
    )

    with pytest.raises(
        RuntimeError,
        match="No parent disk found for root partition /dev/sda1",
    ):
        get_system_disk_by_id()


def test_system_disk_by_id_fails_without_by_id_link(mocker):
    root_partition = mocker.Mock(path="/dev/sda1")
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.BlockDevices",
        return_value=mocker.Mock(get_root_block_device=lambda: root_partition),
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.subprocess.check_output",
        return_value="sda\n",
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.glob.glob",
        return_value=[],
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.os.path.realpath",
        return_value="/dev/sda",
    )

    with pytest.raises(
        RuntimeError,
        match="No supported /dev/disk/by-id link found for system disk /dev/sda",
    ):
        get_system_disk_by_id()


def test_system_disk_by_id_fails_with_unsupported_by_id_link(mocker):
    root_partition = mocker.Mock(path="/dev/sda1")
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.BlockDevices",
        return_value=mocker.Mock(get_root_block_device=lambda: root_partition),
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.subprocess.check_output",
        return_value="sda\n",
    )
    path = "/dev/disk/by-id/virtio-root-disk"
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.glob.glob",
        return_value=[path],
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.os.path.realpath",
        return_value="/dev/sda",
    )

    with pytest.raises(
        RuntimeError,
        match="No supported /dev/disk/by-id link found for system disk /dev/sda",
    ):
        get_system_disk_by_id()


def test_system_disk_by_id_uses_parent_disk_and_ignores_partitions(mocker):
    root_partition = mocker.Mock(path="/dev/sda1")
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.BlockDevices",
        return_value=mocker.Mock(get_root_block_device=lambda: root_partition),
    )
    check_output = mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.subprocess.check_output",
        return_value="sda\n",
    )
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.glob.glob",
        return_value=[
            "/dev/disk/by-id/wwn-0x123-part1",
            "/dev/disk/by-id/virtio-root-disk",
            "/dev/disk/by-id/wwn-0x123",
        ],
    )
    resolved_paths = {
        "/dev/sda": "/dev/sda",
        "/dev/disk/by-id/virtio-root-disk": "/dev/sda",
        "/dev/disk/by-id/wwn-0x123": "/dev/sda",
    }
    mocker.patch(
        "selfprivacy_api.migrations.configure_hetzner_bootloader.os.path.realpath",
        side_effect=lambda path: resolved_paths[path],
    )

    assert get_system_disk_by_id() == "/dev/disk/by-id/wwn-0x123"
    assert check_output.call_args.args[0] == [
        "lsblk",
        "-n",
        "-o",
        "PKNAME",
        "/dev/sda1",
    ]
