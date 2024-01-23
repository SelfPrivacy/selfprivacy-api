"""
Action-level tests of ssh
(For API-independent logic incl. connection to persistent storage)
"""

import pytest
from typing import Optional

from selfprivacy_api.actions.ssh import (
    set_ssh_settings,
    get_ssh_settings,
    create_ssh_key,
    remove_ssh_key,
    KeyNotFound,
    UserNotFound,
)
from selfprivacy_api.actions.users import (
    get_users,
    get_user_by_username,
    UserDataUserOrigin,
)
from selfprivacy_api.utils import WriteUserData, ReadUserData


@pytest.fixture(params=[True, False])
def bool_value(request):
    return request.param


@pytest.fixture(
    params=[
        "normal_populated_json",
        "deleted_enabled",
        "deleted_auth",
        "empty",
        "ssh_not_in_json",
    ]
)
def possibly_undefined_ssh_settings(generic_userdata, request, bool_value):
    with WriteUserData() as data:
        data["ssh"] = {"enable": bool_value, "passswordAuthentication": bool_value}
    assert get_raw_json_ssh_setting("enable") == bool_value
    assert get_raw_json_ssh_setting("passswordAuthentication") == bool_value

    if request.param == "deleted_enabled":
        with WriteUserData() as data:
            del data["ssh"]["enable"]

    if request.param == "deleted_auth":
        with WriteUserData() as data:
            del data["ssh"]["passswordAuthentication"]

    if request.param == "empty":
        with WriteUserData() as data:
            del data["ssh"]["passswordAuthentication"]
            del data["ssh"]["enable"]

    if request.param == "ssh_not_in_json":
        with WriteUserData() as data:
            del data["ssh"]


@pytest.fixture(params=[True, False, None])
def ssh_enable_spectrum(request):
    return request.param


@pytest.fixture(params=[True, False, None])
def password_auth_spectrum(request):
    return request.param


def admin_name() -> Optional[str]:
    users = get_users()
    for user in users:
        if user.origin == UserDataUserOrigin.PRIMARY:
            return user.username
    return None


def get_raw_json_ssh_setting(setting: str):
    with ReadUserData() as data:
        return (data.get("ssh") or {}).get(setting)


def test_read_json(possibly_undefined_ssh_settings):
    with ReadUserData() as data:
        if "ssh" not in data.keys():
            assert get_ssh_settings().enable is not None
            assert get_ssh_settings().passwordAuthentication is not None

            # TODO: Is it really a good idea to have password ssh enabled by default?
            assert get_ssh_settings().enable is True
            assert get_ssh_settings().passwordAuthentication is True
            return

        if "enable" not in data["ssh"].keys():
            assert get_ssh_settings().enable is True
        else:
            assert get_ssh_settings().enable == data["ssh"]["enable"]

        if "passwordAuthentication" not in data["ssh"].keys():
            assert get_ssh_settings().passwordAuthentication is False
        else:
            assert (
                get_ssh_settings().passwordAuthentication
                == data["ssh"]["passwordAuthentication"]
            )


def test_enabling_disabling_writes_json(
    possibly_undefined_ssh_settings, ssh_enable_spectrum, password_auth_spectrum
):
    original_enable = get_raw_json_ssh_setting("enable")
    original_password_auth = get_raw_json_ssh_setting("passwordAuthentication")

    set_ssh_settings(ssh_enable_spectrum, password_auth_spectrum)

    with ReadUserData() as data:
        if ssh_enable_spectrum is None:
            assert get_raw_json_ssh_setting("enable") == original_enable
        else:
            assert get_raw_json_ssh_setting("enable") == ssh_enable_spectrum

        if password_auth_spectrum is None:
            assert (
                get_raw_json_ssh_setting("passwordAuthentication")
                == original_password_auth
            )
        else:
            assert (
                get_raw_json_ssh_setting("passwordAuthentication")
                == password_auth_spectrum
            )


############### ROOTKEYS


def test_read_root_keys_from_json(generic_userdata):
    assert get_ssh_settings().rootKeys == ["ssh-ed25519 KEY test@pc"]
    new_keys = ["ssh-ed25519 KEY test@pc", "ssh-ed25519 KEY2 test@pc"]

    with WriteUserData() as data:
        data["ssh"]["rootKeys"] = new_keys

    assert get_ssh_settings().rootKeys == new_keys

    with WriteUserData() as data:
        del data["ssh"]["rootKeys"]

    assert get_ssh_settings().rootKeys == []

    with WriteUserData() as data:
        del data["ssh"]

    assert get_ssh_settings().rootKeys == []


def test_removing_root_key_writes_json(generic_userdata):
    # generic userdata has a a single root key
    rootkeys = get_ssh_settings().rootKeys
    assert len(rootkeys) == 1
    key1 = rootkeys[0]
    key2 = "ssh-rsa MYSUPERKEY root@pc"

    create_ssh_key("root", key2)
    rootkeys = get_ssh_settings().rootKeys
    assert len(rootkeys) == 2

    remove_ssh_key("root", key2)
    with ReadUserData() as data:
        assert "ssh" in data
        assert "rootKeys" in data["ssh"]
        assert data["ssh"]["rootKeys"] == [key1]

    remove_ssh_key("root", key1)
    with ReadUserData() as data:
        assert "ssh" in data
        assert "rootKeys" in data["ssh"]
        assert data["ssh"]["rootKeys"] == []


def test_remove_root_key_on_undefined(generic_userdata):
    # generic userdata has a a single root key
    rootkeys = get_ssh_settings().rootKeys
    assert len(rootkeys) == 1
    key1 = rootkeys[0]

    with WriteUserData() as data:
        del data["ssh"]["rootKeys"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key("root", key1)
    rootkeys = get_ssh_settings().rootKeys
    assert len(rootkeys) == 0

    with WriteUserData() as data:
        del data["ssh"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key("root", key1)
    rootkeys = get_ssh_settings().rootKeys
    assert len(rootkeys) == 0


def test_adding_root_key_writes_json(generic_userdata):
    with WriteUserData() as data:
        del data["ssh"]
    key1 = "ssh-ed25519 KEY test@pc"
    key2 = "ssh-ed25519 KEY2 test@pc"
    create_ssh_key("root", key1)

    with ReadUserData() as data:
        assert "ssh" in data
        assert "rootKeys" in data["ssh"]
        assert data["ssh"]["rootKeys"] == [key1]

    with WriteUserData() as data:
        del data["ssh"]["rootKeys"]
    create_ssh_key("root", key1)

    with ReadUserData() as data:
        assert "ssh" in data
        assert "rootKeys" in data["ssh"]
        assert data["ssh"]["rootKeys"] == [key1]

    create_ssh_key("root", key2)

    with ReadUserData() as data:
        assert "ssh" in data
        assert "rootKeys" in data["ssh"]
        # order is irrelevant
        assert set(data["ssh"]["rootKeys"]) == set([key1, key2])


############### ADMIN KEYS


def test_read_admin_keys_from_json(generic_userdata):
    admin_name = "tester"
    assert get_user_by_username(admin_name).ssh_keys == ["ssh-rsa KEY test@pc"]
    new_keys = ["ssh-rsa KEY test@pc", "ssh-ed25519 KEY2 test@pc"]

    with WriteUserData() as data:
        data["sshKeys"] = new_keys

    assert get_user_by_username(admin_name).ssh_keys == new_keys

    with WriteUserData() as data:
        del data["sshKeys"]

    assert get_user_by_username(admin_name).ssh_keys == []


def test_adding_admin_key_writes_json(generic_userdata):
    admin_name = "tester"

    with WriteUserData() as data:
        del data["sshKeys"]
    key1 = "ssh-ed25519 KEY test@pc"
    key2 = "ssh-ed25519 KEY2 test@pc"
    create_ssh_key(admin_name, key1)

    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == [key1]

    create_ssh_key(admin_name, key2)

    with ReadUserData() as data:
        assert "sshKeys" in data
        # order is irrelevant
        assert set(data["sshKeys"]) == set([key1, key2])


def test_removing_admin_key_writes_json(generic_userdata):
    # generic userdata has a a single admin key
    admin_name = "tester"

    admin_keys = get_user_by_username(admin_name).ssh_keys
    assert len(admin_keys) == 1
    key1 = admin_keys[0]
    key2 = "ssh-rsa MYSUPERKEY admin@pc"

    create_ssh_key(admin_name, key2)
    admin_keys = get_user_by_username(admin_name).ssh_keys
    assert len(admin_keys) == 2

    remove_ssh_key(admin_name, key2)

    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == [key1]

    remove_ssh_key(admin_name, key1)
    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == []


def test_remove_admin_key_on_undefined(generic_userdata):
    # generic userdata has a a single admin key
    admin_name = "tester"

    admin_keys = get_user_by_username(admin_name).ssh_keys
    assert len(admin_keys) == 1
    key1 = admin_keys[0]

    with WriteUserData() as data:
        del data["sshKeys"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key(admin_name, key1)
    admin_keys = get_user_by_username(admin_name).ssh_keys
    assert len(admin_keys) == 0


############### USER KEYS

regular_users = ["user1", "user2", "user3"]


def find_user_index_in_json_users(users: list, username: str) -> Optional[int]:
    for i, user in enumerate(users):
        if user["username"] == username:
            return i
    return None


@pytest.mark.parametrize("username", regular_users)
def test_read_user_keys_from_json(generic_userdata, username):
    old_keys = [f"ssh-rsa KEY {username}@pc"]
    assert get_user_by_username(username).ssh_keys == old_keys
    new_keys = ["ssh-rsa KEY test@pc", "ssh-ed25519 KEY2 test@pc"]

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        data["users"][user_index]["sshKeys"] = new_keys

    assert get_user_by_username(username).ssh_keys == new_keys

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]

    assert get_user_by_username(username).ssh_keys == []

    # deeper deletions are for user getter tests, not here


@pytest.mark.parametrize("username", regular_users)
def test_adding_user_key_writes_json(generic_userdata, username):
    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]
    key1 = "ssh-ed25519 KEY test@pc"
    key2 = "ssh-ed25519 KEY2 test@pc"
    create_ssh_key(username, key1)

    with ReadUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        assert "sshKeys" in data["users"][user_index]
        assert data["users"][user_index]["sshKeys"] == [key1]

    create_ssh_key(username, key2)

    with ReadUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        assert "sshKeys" in data["users"][user_index]
        # order is irrelevant
        assert set(data["users"][user_index]["sshKeys"]) == set([key1, key2])


@pytest.mark.parametrize("username", regular_users)
def test_removing_user_key_writes_json(generic_userdata, username):
    # generic userdata has a a single user key

    user_keys = get_user_by_username(username).ssh_keys
    assert len(user_keys) == 1
    key1 = user_keys[0]
    key2 = "ssh-rsa MYSUPERKEY admin@pc"

    create_ssh_key(username, key2)
    user_keys = get_user_by_username(username).ssh_keys
    assert len(user_keys) == 2

    remove_ssh_key(username, key2)

    with ReadUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        assert "sshKeys" in data["users"][user_index]
        assert data["users"][user_index]["sshKeys"] == [key1]

    remove_ssh_key(username, key1)
    with ReadUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        assert "sshKeys" in data["users"][user_index]
        assert data["users"][user_index]["sshKeys"] == []


@pytest.mark.parametrize("username", regular_users)
def test_remove_user_key_on_undefined(generic_userdata, username):
    # generic userdata has a a single user key
    user_keys = get_user_by_username(username).ssh_keys
    assert len(user_keys) == 1
    key1 = user_keys[0]

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key(username, key1)

    user_keys = get_user_by_username(username).ssh_keys
    assert len(user_keys) == 0

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]

    with pytest.raises(UserNotFound):
        remove_ssh_key(username, key1)

    with WriteUserData() as data:
        del data["users"]

    with pytest.raises(UserNotFound):
        remove_ssh_key(username, key1)
