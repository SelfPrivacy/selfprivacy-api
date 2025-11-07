import pytest
from os import mkdir, rmdir
from os.path import join, exists


from tests.conftest import ensure_user_exists

from selfprivacy_api.services.owned_path import Bind, BindError
from selfprivacy_api.utils.block_devices import BlockDevices


BINDTESTS_USER = "binduser"
TESTFILE_CONTENTS = "testissimo"
TESTFILE_NAME = "testfile"


@pytest.fixture()
def bind_user():
    ensure_user_exists(BINDTESTS_USER)
    return BINDTESTS_USER


def prepare_test_bind(tmpdir, bind_user) -> Bind:
    test_binding_name = "bindy_dir"
    binding_path = join(tmpdir, test_binding_name)
    drive = BlockDevices().get_block_device("sda2")
    assert drive is not None

    bind = Bind(
        binding_path=binding_path, owner=bind_user, group=bind_user, drive=drive
    )

    source_dir = bind.location_at_volume()
    mkdir(source_dir)
    mkdir(binding_path)

    testfile_path = join(source_dir, TESTFILE_NAME)
    with open(testfile_path, "w") as file:
        file.write(TESTFILE_CONTENTS)

    return bind


def test_bind_unbind(
    volume_folders, tmpdir, bind_user, mock_lsblk_devices, generic_userdata
):
    bind = prepare_test_bind(tmpdir, bind_user)
    bind.ensure_ownership()
    bind.validate()

    testfile_path = join(bind.location_at_volume(), TESTFILE_NAME)
    assert exists(testfile_path)
    with open(testfile_path, "r") as file:
        assert file.read() == TESTFILE_CONTENTS

    bind.bind()

    testfile_binding_path = join(bind.binding_path, TESTFILE_NAME)
    assert exists(testfile_path)
    with open(testfile_path, "r") as file:
        assert file.read() == TESTFILE_CONTENTS

    bind.unbind()
    # wait_until_true(lambda : not exists(testfile_binding_path), timeout_sec=2)
    assert not exists(testfile_binding_path)
    assert exists(bind.binding_path)


def test_bind_nonexistent_target(
    volume_folders, tmpdir, bind_user, mock_lsblk_devices, generic_userdata
):
    bind = prepare_test_bind(tmpdir, bind_user)

    bind.ensure_ownership()
    bind.validate()
    rmdir(bind.binding_path)

    with pytest.raises(BindError):
        bind.bind()


def test_unbind_nonexistent_target(
    volume_folders, tmpdir, bind_user, mock_lsblk_devices, generic_userdata
):
    bind = prepare_test_bind(tmpdir, bind_user)

    bind.ensure_ownership()
    bind.validate()
    bind.bind()

    bind.binding_path = "/bogus"

    with pytest.raises(BindError):
        bind.unbind()
