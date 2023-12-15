# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from selfprivacy_api.graphql.mutations.system_mutations import SystemMutations
from selfprivacy_api.graphql.queries.system import System

from tests.common import read_json, generate_system_query
from tests.test_graphql.common import assert_empty, assert_ok, get_data


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


# TESTS ########################################################


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


def api_ssh_settings(authorized_client):
    response = authorized_client.post(
        "/graphql",
        json={"query": generate_system_query([API_SSH_SETTINGS_QUERY])},
    )
    data = get_data(response)
    result = data["system"]["settings"]["ssh"]
    assert result is not None
    return result


def api_set_ssh_settings(authorized_client, enable: bool, password_auth: bool):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_SSH_SETTINGS,
            "variables": {
                "settings": {
                    "enable": enable,
                    "passwordAuthentication": password_auth,
                },
            },
        },
    )
    data = get_data(response)
    result = data["system"]["changeSshSettings"]
    assert result is not None
    return result


def test_graphql_ssh_query(authorized_client, some_users):
    settings = api_ssh_settings(authorized_client)
    assert settings["enable"] is True
    assert settings["passwordAuthentication"] is True


def test_graphql_change_ssh_settings_unauthorized(
    client, some_users, mock_subprocess_popen
):
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


def test_graphql_disable_enable_ssh(
    authorized_client, some_users, mock_subprocess_popen
):
    output = api_set_ssh_settings(authorized_client, enable=False, password_auth=False)
    assert_ok(output)
    assert output["enable"] is False
    assert output["passwordAuthentication"] is False
    assert_includes(api_ssh_settings(authorized_client), output)

    output = api_set_ssh_settings(authorized_client, enable=True, password_auth=True)
    assert_ok(output)
    assert output["enable"] is True
    assert output["passwordAuthentication"] is True
    assert_includes(api_ssh_settings(authorized_client), output)

    output = api_set_ssh_settings(authorized_client, enable=True, password_auth=False)
    assert_ok(output)
    assert output["enable"] is True
    assert output["passwordAuthentication"] is False
    assert_includes(api_ssh_settings(authorized_client), output)

    output = api_set_ssh_settings(authorized_client, enable=False, password_auth=True)
    assert_ok(output)
    assert output["enable"] is False
    assert output["passwordAuthentication"] is True
    assert_includes(api_ssh_settings(authorized_client), output)


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


def test_graphql_add_ssh_key(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
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
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["addSshKey"]["code"] == 201
    assert response.json()["data"]["users"]["addSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["addSshKey"]["success"] is True

    assert response.json()["data"]["users"]["addSshKey"]["user"]["username"] == "user1"
    assert response.json()["data"]["users"]["addSshKey"]["user"]["sshKeys"] == [
        "ssh-rsa KEY user1@pc",
        "ssh-rsa KEY test_key@pc",
    ]


def test_graphql_add_root_ssh_key(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "root",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["addSshKey"]["code"] == 201
    assert response.json()["data"]["users"]["addSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["addSshKey"]["success"] is True

    assert response.json()["data"]["users"]["addSshKey"]["user"]["username"] == "root"
    assert response.json()["data"]["users"]["addSshKey"]["user"]["sshKeys"] == [
        "ssh-ed25519 KEY test@pc",
        "ssh-rsa KEY test_key@pc",
    ]


def test_graphql_add_main_ssh_key(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_SSH_KEY_MUTATION,
            "variables": {
                "sshInput": {
                    "username": "tester",
                    "sshKey": "ssh-rsa KEY test_key@pc",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["addSshKey"]["code"] == 201
    assert response.json()["data"]["users"]["addSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["addSshKey"]["success"] is True

    assert response.json()["data"]["users"]["addSshKey"]["user"]["username"] == "tester"
    assert response.json()["data"]["users"]["addSshKey"]["user"]["sshKeys"] == [
        "ssh-rsa KEY test@pc",
        "ssh-rsa KEY test_key@pc",
    ]


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


def test_graphql_remove_root_ssh_key(
    authorized_client, some_users, mock_subprocess_popen
):
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


def test_graphql_remove_nonexistent_ssh_key(
    authorized_client, some_users, mock_subprocess_popen
):
    response = authorized_client.post(
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
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["removeSshKey"]["code"] == 404
    assert response.json()["data"]["users"]["removeSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["removeSshKey"]["success"] is False


def test_graphql_remove_ssh_key_nonexistent_user(
    authorized_client, some_users, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_REMOVE_SSH_KEY_MUTATION,
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

    assert response.json()["data"]["users"]["removeSshKey"]["code"] == 404
    assert response.json()["data"]["users"]["removeSshKey"]["message"] is not None
    assert response.json()["data"]["users"]["removeSshKey"]["success"] is False
