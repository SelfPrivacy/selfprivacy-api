# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.replace_blockdevices_to_uuid import (
    ReplaceBlockDevicesToUUID,
)
from selfprivacy_api.utils import ReadUserData, WriteUserData

from tests.test_migrations.conftest import ROOT_UUID, VOLUME_UUID


async def test_needed_when_root_partition_missing(generic_userdata):
    # turned_on.json has server.rootPartitionName but no server.rootPartition
    assert await ReplaceBlockDevicesToUUID().is_migration_needed() is True


async def test_not_needed_when_root_partition_set(generic_userdata):
    with WriteUserData() as data:
        data["server"]["rootPartition"] = f"/dev/disk/by-uuid/{ROOT_UUID}"

    assert await ReplaceBlockDevicesToUUID().is_migration_needed() is False


async def test_migrate_writes_uuid_paths(block_devices):
    migration = ReplaceBlockDevicesToUUID()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    with ReadUserData() as data:
        assert data["server"]["rootPartition"] == f"/dev/disk/by-uuid/{ROOT_UUID}"
        assert data["server"]["rootPartitionName"] == "sda1"
        assert data["volumes"] == [
            {
                "device": f"/dev/disk/by-uuid/{VOLUME_UUID}",
                "mountPoint": "/volumes/sdb",
                "fsType": "ext4",
            }
        ]
    assert await migration.is_migration_needed() is False


async def test_migrate_preserves_unmatched_volumes(block_devices):
    # A volume whose device does not match any current partition path
    # (e.g. already recorded by UUID) must survive the migration.
    already_migrated = {
        "device": f"/dev/disk/by-uuid/{VOLUME_UUID}",
        "mountPoint": "/volumes/sdb",
        "fsType": "ext4",
    }
    with WriteUserData() as data:
        data["volumes"] = [already_migrated]

    await ReplaceBlockDevicesToUUID().migrate()

    with ReadUserData() as data:
        assert data["volumes"] == [already_migrated]
