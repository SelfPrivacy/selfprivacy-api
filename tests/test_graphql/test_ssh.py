# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest
from typing import Optional

from selfprivacy_api.graphql.mutations.system_mutations import SystemMutations
from selfprivacy_api.graphql.queries.system import System

# only allowed in fixtures and utils
from selfprivacy_api.actions.ssh import remove_ssh_key, get_ssh_settings
from selfprivacy_api.actions.users import get_users, UserDataUserOrigin

from tests.common import read_json, generate_system_query, generate_users_query
from tests.test_graphql.common import (
    assert_empty,
    assert_ok,
    get_data,
    assert_errorcode,
)
from tests.test_graphql.test_users import API_USERS_INFO

key_users = ["root", "tester", "user1"]


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate(self):  # pylint: disable=no-method-argument
        return (b"NEW_HASHED", None)

    returncode = 0


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def some_users(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "some_users.json")
    assert read_json(datadir / "some_users.json")["users"] == [
        {
            "username": "user1",
            "hashedPassword": "HASHED_PASSWORD_1",
            "sshKeys": ["ssh-rsa KEY user1@pc"],
        },
        {"username": "user2", "hashedPassword": "HASHED_PASSWORD_2", "sshKeys": []},
        {"username": "user3", "hashedPassword": "HASHED_PASSWORD_3"},
    ]
    return datadir


@pytest.fixture
def no_rootkeys(generic_userdata):
    for rootkey in get_ssh_settings().rootKeys:
        remove_ssh_key("root", rootkey)
    assert get_ssh_settings().rootKeys == []


@pytest.fixture
def no_keys(generic_userdata):
    # this removes root and admin keys too

    users = get_users()
    for user in users:
        for key in user.ssh_keys:
            remove_ssh_key(user.username, key)
    users = get_users()
    for user in users:
        assert user.ssh_keys == []


@pytest.fixture
def no_admin_key(generic_userdata, authorized_client):
    admin_keys = api_get_user_keys(authorized_client, admin_name())

    for admin_key in admin_keys:
        remove_ssh_key(admin_name(), admin_key)

    assert api_get_user_keys(authorized_client, admin_name()) == []


def admin_name() -> Optional[str]:
    users = get_users()
    for user in users:
        if user.origin == UserDataUserOrigin.PRIMARY:
            return user.username
    return None


def api_get_user_keys(authorized_client, user: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    data = get_data(response)["users"]["allUsers"]
    for _user in data:
        if _user["username"] == user:
            return _user["sshKeys"]
    return None


API_CREATE_SSH_KEY_MUTATION = """
mutation addSshKey($sshInput: SshMutationInput!) {
    users {
        addSshKey(sshInput: $sshInput) {
            success
            message
            code
            user {
                username
                sshKeys
            }
        }
    }
}
"""

API_SET_SSH_SETTINGS = """
mutation enableSsh($settings: SSHSettingsInput!) {
    system {
        changeSshSettings(settings: $settings) {
            success
            message
            code
            enable
            passwordAuthentication
        }
    }
}

"""

API_SSH_SETTINGS_QUERY = """
settings {
    ssh {
        enable
        passwordAuthentication
    }
}
"""


API_ROOTKEYS_QUERY = """
settings {
    ssh {
        rootSshKeys
    }
}
"""


def api_ssh_settings_raw(client):
    return client.post(
        "/graphql",
        json={"query": generate_system_query([API_SSH_SETTINGS_QUERY])},
    )


def api_rootkeys_raw(client):
    return client.post(
        "/graphql",
        json={"query": generate_system_query([API_ROOTKEYS_QUERY])},
    )


def api_add_ssh_key(authorized_client, user: str, key: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": user,
                    "sshKey": key,
                },
            },
        },
    )
    data = get_data(response)
    result = data["users"]["addSshKey"]
    assert result is not None
    return result


def api_remove_ssh_key(authorized_client, user: str, key: str):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": user,
                    "sshKey": key,
                },
            },
        },
    )
    data = get_data(response)
    result = data["users"]["removeSshKey"]
    assert result is not None
    return result


def api_rootkeys(authorized_client):
    response = api_rootkeys_raw(authorized_client)
    data = get_data(response)
    result = data["system"]["settings"]["ssh"]["rootSshKeys"]
    assert result is not None
    return result


def api_ssh_settings(authorized_client):
    response = api_ssh_settings_raw(authorized_client)
    data = get_data(response)
    result = data["system"]["settings"]["ssh"]
    assert result is not None
    return result


def api_set_ssh_settings_dict(authorized_client, dict):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_SSH_SETTINGS,
            "variables": {
                "settings": dict,
            },
        },
    )
    data = get_data(response)
    result = data["system"]["changeSshSettings"]
    assert result is not None
    return result


def api_set_ssh_settings(authorized_client, enable: bool, password_auth: bool):
    return api_set_ssh_settings_dict(
        authorized_client,
        {
            "enable": enable,
            "passwordAuthentication": password_auth,
        },
    )


# TESTS ########################################################


def test_graphql_ssh_query(authorized_client, some_users):
    settings = api_ssh_settings(authorized_client)
    assert settings["enable"] is True
    assert settings["passwordAuthentication"] is True


def test_graphql_get_ssh_settings_unauthorized(client, some_users):
    response = api_ssh_settings_raw(client)
    assert_empty(response)


def test_graphql_change_ssh_settings_unauthorized(client, some_users):
    response = client.post(
        "/graphql",
        json={
            "query": API_SET_SSH_SETTINGS,
            "variables": {
                "sshInput": {
                    "enable": True,
                    "passwordAuthentication": True,
                },
            },
        },
    )
    assert_empty(response)


def assert_includes(smaller_dict: dict, bigger_dict: dict):
    for item in smaller_dict.items():
        assert item in bigger_dict.items()


available_settings = [
    {"enable": True, "passwordAuthentication": True},
    {"enable": True, "passwordAuthentication": False},
    {"enable": False, "passwordAuthentication": True},
    {"enable": False, "passwordAuthentication": False},
]


original_settings = [
    {"enable": True, "passwordAuthentication": True},
    {"enable": True, "passwordAuthentication": False},
    {"enable": False, "passwordAuthentication": True},
    {"enable": False, "passwordAuthentication": False},
]


@pytest.mark.parametrize("original_settings", original_settings)
@pytest.mark.parametrize("settings", available_settings)
def test_graphql_readwrite_ssh_settings(
    authorized_client, some_users, settings, original_settings
):

    # Userdata-related tests like undefined fields are in actions-level tests.
    output = api_set_ssh_settings_dict(authorized_client, original_settings)
    assert_includes(api_ssh_settings(authorized_client), output)

    output = api_set_ssh_settings_dict(authorized_client, settings)
    assert_ok(output)
    assert_includes(settings, output)
    if "enable" not in settings.keys():
        assert output["enable"] == original_settings["enable"]
    assert_includes(api_ssh_settings(authorized_client), output)


forbidden_settings = [
    # we include this here so that if the next version makes the fields
    # optional, the tests will remind the person that tests are to be extended accordingly
    {"enable": True},
    {"passwordAuthentication": True},
]


@pytest.mark.parametrize("original_settings", original_settings)
@pytest.mark.parametrize("settings", forbidden_settings)
def test_graphql_readwrite_ssh_settings_partial(
    authorized_client, some_users, settings, original_settings
):

    output = api_set_ssh_settings_dict(authorized_client, original_settings)
    with pytest.raises(Exception):
        output = api_set_ssh_settings_dict(authorized_client, settings)


def test_graphql_disable_twice(authorized_client, some_users):
    output = api_set_ssh_settings(authorized_client, enable=False, password_auth=False)
    assert_ok(output)
    assert output["enable"] is False
    assert output["passwordAuthentication"] is False

    output = api_set_ssh_settings(authorized_client, enable=False, password_auth=False)
    assert_ok(output)
    assert output["enable"] is False
    assert output["passwordAuthentication"] is False


def test_graphql_enable_twice(authorized_client, some_users):
    output = api_set_ssh_settings(authorized_client, enable=True, password_auth=True)
    assert_ok(output)
    assert output["enable"] is True
    assert output["passwordAuthentication"] is True
    assert_includes(api_ssh_settings(authorized_client), output)

    output = api_set_ssh_settings(authorized_client, enable=True, password_auth=True)
    assert_ok(output)
    assert output["enable"] is True
    assert output["passwordAuthentication"] is True
    assert_includes(api_ssh_settings(authorized_client), output)


############## KEYS


def test_graphql_add_ssh_key_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user1",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert_empty(response)


# Unauth getting of keys is tested in test_users.py because it is a part of users interface


def test_graphql_get_root_key(authorized_client, some_users):
    assert api_rootkeys(authorized_client) == ["ssh-ed25519 KEY test@pc"]


def test_graphql_get_root_key_when_none(authorized_client, no_rootkeys):
    assert api_rootkeys(authorized_client) == []


# Getting admin keys when they are present is tested in test_users.py


def test_get_admin_key_when_none(authorized_client, no_admin_key):
    assert api_get_user_keys(authorized_client, admin_name()) == []


@pytest.mark.parametrize("user", key_users)
def test_graphql_add_ssh_key_when_none(authorized_client, no_keys, user):
    key1 = "ssh-rsa KEY test_key@pc"
    if user == "root":
        assert api_rootkeys(authorized_client) == []
    else:
        assert api_get_user_keys(authorized_client, user) == []

    output = api_add_ssh_key(authorized_client, user, key1)

    assert output["code"] == 201
    assert output["message"] is not None
    assert output["success"] is True

    assert output["user"]["username"] == user
    assert output["user"]["sshKeys"] == [key1]

    if user == "root":
        assert api_rootkeys(authorized_client) == [key1]
    else:
        assert api_get_user_keys(authorized_client, user) == [key1]


def test_graphql_add_root_ssh_key_one_more(authorized_client, no_rootkeys):
    output = api_add_ssh_key(authorized_client, "root", "ssh-rsa KEY test_key@pc")
    assert output["user"]["sshKeys"] == ["ssh-rsa KEY test_key@pc"]

    output = api_add_ssh_key(authorized_client, "root", "ssh-rsa KEY2 test_key@pc")
    assert output["code"] == 201
    assert output["message"] is not None
    assert output["success"] is True

    assert output["user"]["username"] == "root"

    expected_keys = [
        "ssh-rsa KEY test_key@pc",
        "ssh-rsa KEY2 test_key@pc",
    ]

    assert output["user"]["sshKeys"] == expected_keys
    assert api_rootkeys(authorized_client) == expected_keys


def test_graphql_add_root_ssh_key_same(authorized_client, no_rootkeys):
    key = "ssh-rsa KEY test_key@pc"
    output = api_add_ssh_key(authorized_client, "root", key)
    assert output["user"]["sshKeys"] == [key]

    output = api_add_ssh_key(authorized_client, "root", key)
    assert_errorcode(output, 409)


# TODO: multiplex for root and admin
def test_graphql_add_bad_ssh_key(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user1",
                    "sshKey": "trust me, this is the ssh key",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["addSshKey"]["code"] == 400
    assert response.json()["data"]["users"]["addSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["addSshKey"]["success"] is False


def test_graphql_add_ssh_key_nonexistent_user(
    authorized_client, some_users, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user666",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["addSshKey"]["code"] == 404
    assert response.json()["data"]["users"]["addSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["addSshKey"]["success"] is False


API_REMOVE_SSH_KEY_MUTATION = """
mutation removeSshKey($sshInput: SshMutationInput!) {
    users {
        removeSshKey(sshInput: $sshInput) {
            success
            message
            code
            user {
                username
                sshKeys
            }
        }
    }
}
"""


def test_graphql_remove_ssh_key_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user1",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert_empty(response)


def test_graphql_remove_ssh_key(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "user1",
                    "sshKey": "ssh-rsa KEY user1@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["removeSshKey"]["code"] == 200
    assert response.json()["data"]["users"]["removeSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["removeSshKey"]["success"] is True

    assert (
        response.json()["data"]["users"]["removeSshKey"]["user"]["username"] == "user1"
    )
    assert response.json()["data"]["users"]["removeSshKey"]["user"]["sshKeys"] == []


def test_graphql_remove_root_ssh_key(authorized_client, some_users):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "root",
                    "sshKey": "ssh-ed25519 KEY test@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["removeSshKey"]["code"] == 200
    assert response.json()["data"]["users"]["removeSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["removeSshKey"]["success"] is True

    assert (
        response.json()["data"]["users"]["removeSshKey"]["user"]["username"] == "root"
    )
    assert response.json()["data"]["users"]["removeSshKey"]["user"]["sshKeys"] == []


def test_graphql_remove_main_ssh_key(
    authorized_client, some_users, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "tester",
                    "sshKey": "ssh-rsa KEY test@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["removeSshKey"]["code"] == 200
    assert response.json()["data"]["users"]["removeSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["removeSshKey"]["success"] is True

    assert (
        response.json()["data"]["users"]["removeSshKey"]["user"]["username"] == "tester"
    )
    assert response.json()["data"]["users"]["removeSshKey"]["user"]["sshKeys"] == []


@pytest.mark.parametrize("user", key_users)
def test_graphql_remove_nonexistent_ssh_key(authorized_client, some_users, user):
    output = api_remove_ssh_key(authorized_client, user, "ssh-rsa nonexistent")
    assert_errorcode(output, 404)


def test_graphql_remove_ssh_key_nonexistent_user(
    authorized_client, some_users, mock_subprocess_popen
):
    output = api_remove_ssh_key(authorized_client, "user666", "ssh-rsa KEY test_key@pc")
    assert_errorcode(output, 404)
