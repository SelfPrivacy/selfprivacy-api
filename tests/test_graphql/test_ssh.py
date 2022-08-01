# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from tests.common import read_json


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
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
"""


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
    assert response.status_code == 200
    assert response.json.get("data") is None


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
    assert response.json.get("data") is not None

    assert response.json["data"]["addSshKey"]["code"] == 201
    assert response.json["data"]["addSshKey"]["message"] is not None
    assert response.json["data"]["addSshKey"]["success"] is True

    assert response.json["data"]["addSshKey"]["user"]["username"] == "user1"
    assert response.json["data"]["addSshKey"]["user"]["sshKeys"] == [
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
    assert response.json.get("data") is not None

    assert response.json["data"]["addSshKey"]["code"] == 201
    assert response.json["data"]["addSshKey"]["message"] is not None
    assert response.json["data"]["addSshKey"]["success"] is True

    assert response.json["data"]["addSshKey"]["user"]["username"] == "root"
    assert response.json["data"]["addSshKey"]["user"]["sshKeys"] == [
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
    assert response.json.get("data") is not None

    assert response.json["data"]["addSshKey"]["code"] == 201
    assert response.json["data"]["addSshKey"]["message"] is not None
    assert response.json["data"]["addSshKey"]["success"] is True

    assert response.json["data"]["addSshKey"]["user"]["username"] == "tester"
    assert response.json["data"]["addSshKey"]["user"]["sshKeys"] == [
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
    assert response.json.get("data") is not None

    assert response.json["data"]["addSshKey"]["code"] == 400
    assert response.json["data"]["addSshKey"]["message"] is not None
    assert response.json["data"]["addSshKey"]["success"] is False


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
    assert response.json.get("data") is not None

    assert response.json["data"]["addSshKey"]["code"] == 404
    assert response.json["data"]["addSshKey"]["message"] is not None
    assert response.json["data"]["addSshKey"]["success"] is False


API_REMOVE_SSH_KEY_MUTATION = """
mutation removeSshKey($sshInput: SshMutationInput!) {
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
    assert response.status_code == 200
    assert response.json.get("data") is None


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
    assert response.json.get("data") is not None

    assert response.json["data"]["removeSshKey"]["code"] == 200
    assert response.json["data"]["removeSshKey"]["message"] is not None
    assert response.json["data"]["removeSshKey"]["success"] is True

    assert response.json["data"]["removeSshKey"]["user"]["username"] == "user1"
    assert response.json["data"]["removeSshKey"]["user"]["sshKeys"] == []


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
    assert response.json.get("data") is not None

    assert response.json["data"]["removeSshKey"]["code"] == 200
    assert response.json["data"]["removeSshKey"]["message"] is not None
    assert response.json["data"]["removeSshKey"]["success"] is True

    assert response.json["data"]["removeSshKey"]["user"]["username"] == "root"
    assert response.json["data"]["removeSshKey"]["user"]["sshKeys"] == []


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
    assert response.json.get("data") is not None

    assert response.json["data"]["removeSshKey"]["code"] == 200
    assert response.json["data"]["removeSshKey"]["message"] is not None
    assert response.json["data"]["removeSshKey"]["success"] is True

    assert response.json["data"]["removeSshKey"]["user"]["username"] == "tester"
    assert response.json["data"]["removeSshKey"]["user"]["sshKeys"] == []


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
    assert response.json.get("data") is not None

    assert response.json["data"]["removeSshKey"]["code"] == 404
    assert response.json["data"]["removeSshKey"]["message"] is not None
    assert response.json["data"]["removeSshKey"]["success"] is False


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
    assert response.json.get("data") is not None

    assert response.json["data"]["removeSshKey"]["code"] == 404
    assert response.json["data"]["removeSshKey"]["message"] is not None
    assert response.json["data"]["removeSshKey"]["success"] is False
