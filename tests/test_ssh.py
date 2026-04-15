"""
Action-level tests of ssh
(For API-independent logic incl. connection to persistent storage)
"""

import base64
from typing import Optional

import pytest

from selfprivacy_api.actions.ssh import (
    KeyNotFound,
    UserNotFound,
    create_ssh_key,
    get_ssh_settings,
    remove_ssh_key,
)
from selfprivacy_api.exceptions.users import UserNotFound
from selfprivacy_api.exceptions.users.ssh import KeyNotFound
from selfprivacy_api.models.user import UserDataUserOrigin
from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.ssh import validate_ssh_public_key


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


def get_raw_json_ssh_setting(setting: str):
    with ReadUserData() as data:
        return (data.get("ssh") or {}).get(setting)


def test_read_json(possibly_undefined_ssh_settings):
    with ReadUserData() as data:
        if "ssh" not in data.keys():
            assert get_ssh_settings().enable is not None
            assert get_ssh_settings().passwordAuthentication is not None

            assert get_ssh_settings().enable is True
            assert get_ssh_settings().passwordAuthentication is False
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


############### ROOTKEYS


def test_read_root_keys_from_json(generic_userdata):
    assert get_ssh_settings().rootKeys == [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIElWG9GbP2g8Jsy/N01w1wjRvBxsNLWxr9NasN694kYw testkey"
    ]
    new_keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIElWG9GbP2g8Jsy/N01w1wjRvBxsNLWxr9NasN694kYw testkey",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2",
    ]

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
    key2 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLETpmvz8G0fOsl6Kx01xXWO75FTzOFTXceibYegLNNrJ5BV3AYGaNwyMLbI11rmeYH9Nk33jtej1upJWXkRwVM= adminsuperkey"

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
    key1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIElWG9GbP2g8Jsy/N01w1wjRvBxsNLWxr9NasN694kYw testkey"
    key2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2"
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


@pytest.mark.asyncio
async def test_read_admin_keys_from_json(generic_userdata):
    admin_name = "tester"
    assert (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys == [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHptiXtnh0b57aK6B117g+CkINlbx8JSTl03Ry0/a2BB dummykey"
    ]
    new_keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHptiXtnh0b57aK6B117g+CkINlbx8JSTl03Ry0/a2BB dummykey",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2",
    ]

    with WriteUserData() as data:
        data["sshKeys"] = new_keys

    assert (
        await JsonUserRepository.get_user_by_username(admin_name)
    ).ssh_keys == new_keys

    with WriteUserData() as data:
        del data["sshKeys"]

    assert (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys == []


def test_adding_admin_key_writes_json(generic_userdata):
    admin_name = "tester"

    with WriteUserData() as data:
        del data["sshKeys"]
    key1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIElWG9GbP2g8Jsy/N01w1wjRvBxsNLWxr9NasN694kYw testkey"
    key2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2"
    create_ssh_key(admin_name, key1)

    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == [key1]

    create_ssh_key(admin_name, key2)

    with ReadUserData() as data:
        assert "sshKeys" in data
        # order is irrelevant
        assert set(data["sshKeys"]) == set([key1, key2])


@pytest.mark.asyncio
async def test_removing_admin_key_writes_json(generic_userdata):
    # generic userdata has a a single admin key
    admin_name = "tester"

    admin_keys = (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys
    assert len(admin_keys) == 1
    key1 = admin_keys[0]
    key2 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLETpmvz8G0fOsl6Kx01xXWO75FTzOFTXceibYegLNNrJ5BV3AYGaNwyMLbI11rmeYH9Nk33jtej1upJWXkRwVM= adminsuperkey"

    create_ssh_key(admin_name, key2)
    admin_keys = (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys
    assert len(admin_keys) == 2

    remove_ssh_key(admin_name, key2)

    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == [key1]

    remove_ssh_key(admin_name, key1)
    with ReadUserData() as data:
        assert "sshKeys" in data
        assert data["sshKeys"] == []


@pytest.mark.asyncio
async def test_remove_admin_key_on_undefined(generic_userdata):
    # generic userdata has a a single admin key
    admin_name = "tester"

    admin_keys = (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys
    assert len(admin_keys) == 1
    key1 = admin_keys[0]

    with WriteUserData() as data:
        del data["sshKeys"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key(admin_name, key1)
    admin_keys = (await JsonUserRepository.get_user_by_username(admin_name)).ssh_keys
    assert len(admin_keys) == 0


############### USER KEYS

regular_users = ["user1", "user2", "user3"]


def find_user_index_in_json_users(users: list, username: str) -> Optional[int]:
    for i, user in enumerate(users):
        if user["username"] == username:
            return i
    return None


@pytest.mark.parametrize("username", regular_users)
@pytest.mark.asyncio
async def test_read_user_keys_from_json(generic_userdata, username):
    old_keys = [
        f"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGouijZuaO6EKh1wZypWvCgQOxSnjnZ52z5hITM2R9MR {username}"
    ]
    assert (
        await JsonUserRepository.get_user_by_username(username)
    ).ssh_keys == old_keys
    new_keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHptiXtnh0b57aK6B117g+CkINlbx8JSTl03Ry0/a2BB dummykey",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2",
    ]

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        data["users"][user_index]["sshKeys"] = new_keys

    assert (
        await JsonUserRepository.get_user_by_username(username)
    ).ssh_keys == new_keys

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]

    assert (await JsonUserRepository.get_user_by_username(username)).ssh_keys == []

    # deeper deletions are for user getter tests, not here


@pytest.mark.parametrize("username", regular_users)
def test_adding_user_key_writes_json(generic_userdata, username):
    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]
    key1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIElWG9GbP2g8Jsy/N01w1wjRvBxsNLWxr9NasN694kYw testkey"
    key2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF6BiRj38tAIEyxA4Ek6Yvc4MhP2NRjKE2s4Lq/v+sK1 testkey2"
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
@pytest.mark.asyncio
async def test_removing_user_key_writes_json(generic_userdata, username):
    # generic userdata has a a single user key

    user_keys = (await JsonUserRepository.get_user_by_username(username)).ssh_keys
    assert len(user_keys) == 1
    key1 = user_keys[0]
    key2 = "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLETpmvz8G0fOsl6Kx01xXWO75FTzOFTXceibYegLNNrJ5BV3AYGaNwyMLbI11rmeYH9Nk33jtej1upJWXkRwVM= adminsuperkey"

    create_ssh_key(username, key2)
    user_keys = (await JsonUserRepository.get_user_by_username(username)).ssh_keys
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
@pytest.mark.asyncio
async def test_remove_user_key_on_undefined(generic_userdata, username):
    # generic userdata has a a single user key
    user_keys = await JsonUserRepository.get_user_by_username(username)
    user_keys = user_keys.ssh_keys
    assert len(user_keys) == 1
    key1 = user_keys[0]

    with WriteUserData() as data:
        user_index = find_user_index_in_json_users(data["users"], username)
        del data["users"][user_index]["sshKeys"]

    with pytest.raises(KeyNotFound):
        remove_ssh_key(username, key1)

    user_keys = (await JsonUserRepository.get_user_by_username(username)).ssh_keys
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


def test_malformed_key_blob_exceeds_bounds():
    """Test that a crafted key blob with oversized key_type_size returns error."""

    # key_type_size = 100 (big-endian), but actual key_type (ssh-ed25519) size is just 11 bytes.
    malformed_blob = b"\x00\x00\x00\x64" + b"ssh-ed25519"

    b64_blob = base64.b64encode(malformed_blob).decode("ascii")
    malicious_key = f"ssh-ed25519 {b64_blob}"

    result = validate_ssh_public_key(malicious_key)
    assert result is False


def test_validate_ssh_ed25519():
    assert (
        validate_ssh_public_key(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK+y1mUS1rFbuy2V5ndMWBwS4AavxjSt0JQGwUhddu1h user@host"
        )
        is True
    )
    assert (
        validate_ssh_public_key(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK+y1mUS1rFbuy2V5ndMWBwS4AavxjSt0JQGwUhddu1h"
        )
        is True
    )
    assert validate_ssh_public_key("ssh-ed25519 notvalidbase64blob") is False


def test_validate_ssh_rsa():
    assert validate_ssh_public_key("ssh-rsa notvalidbase64blob") is False

    # RSA 1024 bits
    assert (
        validate_ssh_public_key(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQDi3CtYS/gAyWvMbEFmypOdHllyelZjHKlrb56R2moRgOg3aKDDP60rFF1EfzTrlKLq5pZbwJocCARMEDwrfXE1XJUFLTA7V+IAnsUGp7Hi9b7ZmP2VWJXsAi0v+jql0Oi49ZShWcUpufbbf7nScF5EOGRD0yW1wHrZSSZZCRL+pw=="
        )
        is False
    )
    # RSA 2048 bits
    assert (
        validate_ssh_public_key(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZz/Yp5h+qn4NJ35d4yASYUYawABga7Vke8BpCRy6EVNAZusslSk0IjSBtDcCdCFEcZ+KW/d55E3bbWBAiSInPQ0hRFeeyDw34aDAJ+vhJ0CHQYFxSeyknnFIRPBnf8T15M7nlUor3JE1z2atoVwQTojmuqtGGqgoz9IK2GQy2WNw00fWlyh364QVKhIzINA7qi2mAkRpX08w8qmSxPQZC/51CuJ8aUuIIy79saLvRg/69EzPl5yaHwU0w24ivQxgNBr3cOL6tOBZnUZp3ilk6uf/LrpXjxRA9DZmLgS1/2AVEiVCCnIjxcTLlHf8Oqzeb7y5iohasEsh6YfmW42T3"
        )
        is True
    )
    # RSA 3072 bits
    assert (
        validate_ssh_public_key(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCeJuwyezMS+mgeri2kiBsUTPmJd0PoF81Y3ea8/imCT5wLLtSGUk+vl2xwznQVHEpaD9TbIT5uhBFgJA/zmkc/B+cEAUfvs6MM8XhcDe2YECKD7NFHOEMrN745yD0hCvDtsK/YcT7mBWFjXfUl70SPBjUVz3baj4R7M6sBXxj8ZGYJi9SocHJGnpiW/Wjr2/sO4BxqKphmBx6OFeF9h0fw8ZUkE43gDYFyMxKt78+qUo0cScelQDh+p7BzWdloV/ENA46+CcoW7WCr/uTGo0Oa7ECE8Ws+D94TLjgJ0blDAnWJdggbzPoQqBBthKUiMbdBghcj972xx17dfMBlCpCyp9Kj84/SFEWVbkpjfWUjzlHwXvrkxdzY+z05zqMumSP+kF8P0lXVNtYOrOEto9/TZvrnJtG3tOswOj+4acxWgnxcfHKRjaKcyqjeNiEDYxpzm5egfb2PkG11E8171+Xit2ahTLqBDQWW3MdHtLNGJL/f2kp4ygPTSb4NZV4HfY0="
        )
        is True
    )
    # RSA 4096 bits
    assert (
        validate_ssh_public_key(
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC4ImCHXy8c23Q1HVUrLX6ItTL8uKSwcaujBgZ3NSpIk6FsbJhQmhETAdiu6UZRHTZ3Bv3jUmW70sQDd5VS1dNOsqnoU2qFTGlqUKKXh99RgChEuvGndEA1xq5iuxouzOx2P2dcfk6KQEB/Kyoj3dg9JI9MtyeDzTtV+VDrNl75GxfQoZ6cZaIkwDC/3fU71XzizBl4IIjNCQLgSVZ78/AZq5XOxGBGRdRGOeklhGq96A+XlM1hMIEaWJddqFGQwC20aw4jKAzOPnyYJG4/FNlw9pTiMWP20/aEey6uxAgyzrkYHb+6edtM2ouDt+SctuRsNaVD3VyjiXaCw3Hd+8iclpzioFc9ZdExflBENK70AxBZ5/N70RIAPK2X2o/P6xe416fJ00hZon5MX4Mp1W6yRII75HTshqw5R4yJdMPJtmCe8nKbt0jpR4y4fMnfS+aYX471SEvbGK12OniT+kayDa3ZPxGlskX6wQgS+zFkwioRWsk3k++WJc1h2Q/skNrbUpfu6WkS3udJcc8eIXTGD/6Dp5eJAynKkHR6BXJSHXB4lpzdplaE+ETr/yCJaVWIpeZrhJVa0eN/xY7V9qcERMYUabKj4BMcv8n1NQELUPLZtLjz0QOj41n12/RAGNo0JgxWeg+C7GqVwxBnAunxBfHwECDiDM2dlVLewV0oXQ=="
        )
        is True
    )


def test_validate_ssh_ecdsa():
    assert (
        validate_ssh_public_key(
            "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBPPcBYLSjZw1TCE15ghjzLzYJzCdHhhQPCfqYNER615mhzafWsDTXkAQSkSmZv70Fv4fsJ9BNRQY8vnuaBdW7hc="
        )
        is True
    )
    assert (
        validate_ssh_public_key(
            "ecdsa-sha2-nistp384 AAAAE2VjZHNhLXNoYTItbmlzdHAzODQAAAAIbmlzdHAzODQAAABhBOwLA7Z+0dZgAL8Xmshrz4vQ1+c/EQI5UnRg3gA5nJlG8awl33b+Br7FtFM1QhjyJ8nPtqN1+fk/6gY11vHZd4ljSKf6sIU2sc4dKyfzWve+69tVhSwrxKQGz+KWq4gkuA=="
        )
        is True
    )
    assert (
        validate_ssh_public_key(
            "ecdsa-sha2-nistp521 AAAAE2VjZHNhLXNoYTItbmlzdHA1MjEAAAAIbmlzdHA1MjEAAACFBAG+613ehWb/xv4FYXYn5vV5Jaq6sPjtjhRnopQTT8bRiAVstMi+8vTqlatwEj3xlgAyqsKtGs1YiG7aKT39d1kNwQCvrt0P6jvhqcZizgBYn6VCuOJMVMJXxdVbNy65WKcrvDN0XK6qFB9p1fbMgK/rbsTvkUOv597e0OMvDzN7KxYfqQ=="
        )
        is True
    )
