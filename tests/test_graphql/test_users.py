# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from tests.common import (
    generate_users_query,
    read_json,
)

invalid_usernames = [
    "messagebus",
    "postfix",
    "polkituser",
    "dovecot2",
    "dovenull",
    "nginx",
    "postgres",
    "systemd-journal-gateway",
    "prosody",
    "systemd-network",
    "systemd-resolve",
    "systemd-timesync",
    "opendkim",
    "rspamd",
    "sshd",
    "selfprivacy-api",
    "restic",
    "redis",
    "pleroma",
    "ocserv",
    "nextcloud",
    "memcached",
    "knot-resolver",
    "gitea",
    "bitwarden_rs",
    "vaultwarden",
    "acme",
    "virtualMail",
    "nixbld1",
    "nixbld2",
    "nixbld29",
    "nobody",
]


##  FIXTURES  ###################################################


@pytest.fixture
def no_users(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_users.json")
    assert read_json(datadir / "no_users.json")["users"] == []
    return datadir


@pytest.fixture
def one_user(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "one_user.json")
    assert read_json(datadir / "one_user.json")["users"] == [
        {
            "username": "user1",
            "hashedPassword": "HASHED_PASSWORD_1",
            "sshKeys": ["ssh-rsa KEY user1@pc"],
        }
    ]
    return datadir


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
def undefined_settings(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "users" not in read_json(datadir / "undefined.json")
    return datadir


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


##  TESTS  ######################################################

API_USERS_INFO = """
allUsers {
    username
    sshKeys
}
"""


def test_graphql_get_users_unauthorized(client, some_users, mock_subprocess_popen):
    """Test wrong auth"""
    response = client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_get_some_users(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None
    assert len(response.json()["data"]["users"]["allUsers"]) == 4
    assert response.json()["data"]["users"]["allUsers"][0]["username"] == "user1"
    assert response.json()["data"]["users"]["allUsers"][0]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]

    assert response.json()["data"]["users"]["allUsers"][1]["username"] == "user2"
    assert response.json()["data"]["users"]["allUsers"][1]["sshKeys"] == []

    assert response.json()["data"]["users"]["allUsers"][3]["username"] == "tester"
    assert response.json()["data"]["users"]["allUsers"][3]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_no_users(authorized_client, no_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": generate_users_query([API_USERS_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["allUsers"]) == 1
    assert response.json()["data"]["users"]["allUsers"][0]["username"] == "tester"
    assert response.json()["data"]["users"]["allUsers"][0]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


API_GET_USERS = """
query TestUsers($username: String!) {
    users {
        getUser(username: $username) {
            sshKeys
            username
        }
    }
}
"""


def test_graphql_get_one_user_unauthorized(client, one_user, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_get_one_user(authorized_client, one_user, mock_subprocess_popen):

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "user1",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "user1"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]


def test_graphql_get_some_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "user2",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "user2"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == []


def test_graphql_get_root_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "root",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "root"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-ed25519 KEY test@pc"
    ]


def test_graphql_get_main_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "tester",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert len(response.json()["data"]["users"]["getUser"]) == 2
    assert response.json()["data"]["users"]["getUser"]["username"] == "tester"
    assert response.json()["data"]["users"]["getUser"]["sshKeys"] == [
        "ssh-rsa KEY test@pc"
    ]


def test_graphql_get_nonexistent_user(
    authorized_client, one_user, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_USERS,
            "variables": {
                "username": "tyler_durden",
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["getUser"] is None


API_CREATE_USERS_MUTATION = """
mutation createUser($user: UserMutationInput!) {
    users {
        createUser(user: $user) {
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


def test_graphql_add_user_unauthorize(client, one_user, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "user2",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_add_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "user2",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 201
    assert response.json()["data"]["users"]["createUser"]["success"] is True

    assert response.json()["data"]["users"]["createUser"]["user"]["username"] == "user2"
    assert response.json()["data"]["users"]["createUser"]["user"]["sshKeys"] == []


def test_graphql_add_undefined_settings(
    authorized_client, undefined_settings, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "user2",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 201
    assert response.json()["data"]["users"]["createUser"]["success"] is True

    assert response.json()["data"]["users"]["createUser"]["user"]["username"] == "user2"
    assert response.json()["data"]["users"]["createUser"]["user"]["sshKeys"] == []


def test_graphql_add_without_password(
    authorized_client, one_user, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "user2",
                    "password": "",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 400
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"] is None


def test_graphql_add_without_both(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "",
                    "password": "",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 400
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"] is None


@pytest.mark.parametrize("username", invalid_usernames)
def test_graphql_add_system_username(
    authorized_client, one_user, mock_subprocess_popen, username
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": username,
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 409
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"] is None


def test_graphql_add_existing_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 409
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"]["username"] == "user1"
    assert (
        response.json()["data"]["users"]["createUser"]["user"]["sshKeys"][0]
        == "ssh-rsa KEY user1@pc"
    )


def test_graphql_add_main_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "tester",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 409
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert (
        response.json()["data"]["users"]["createUser"]["user"]["username"] == "tester"
    )
    assert (
        response.json()["data"]["users"]["createUser"]["user"]["sshKeys"][0]
        == "ssh-rsa KEY test@pc"
    )


def test_graphql_add_long_username(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": "a" * 32,
                    "password": "12345678",
                },
            },
        },
    )
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 400
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"] is None


@pytest.mark.parametrize("username", ["", "1", "фыр", "user1@", "^-^"])
def test_graphql_add_invalid_username(
    authorized_client, one_user, mock_subprocess_popen, username
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CREATE_USERS_MUTATION,
            "variables": {
                "user": {
                    "username": username,
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["createUser"]["message"] is not None
    assert response.json()["data"]["users"]["createUser"]["code"] == 400
    assert response.json()["data"]["users"]["createUser"]["success"] is False

    assert response.json()["data"]["users"]["createUser"]["user"] is None


API_DELETE_USER_MUTATION = """
mutation deleteUser($username: String!) {
    users {
        deleteUser(username: $username) {
            success
            message
            code
        }
    }
}
"""


def test_graphql_delete_user_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "user1"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_delete_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "user1"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 200
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is True


@pytest.mark.parametrize("username", ["", "def"])
def test_graphql_delete_nonexistent_users(
    authorized_client, some_users, mock_subprocess_popen, username
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": username},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 404
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


@pytest.mark.parametrize("username", invalid_usernames)
def test_graphql_delete_system_users(
    authorized_client, some_users, mock_subprocess_popen, username
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": username},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert (
        response.json()["data"]["users"]["deleteUser"]["code"] == 404
        or response.json()["data"]["users"]["deleteUser"]["code"] == 400
    )
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


def test_graphql_delete_main_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DELETE_USER_MUTATION,
            "variables": {"username": "tester"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["deleteUser"]["code"] == 400
    assert response.json()["data"]["users"]["deleteUser"]["message"] is not None
    assert response.json()["data"]["users"]["deleteUser"]["success"] is False


API_UPDATE_USER_MUTATION = """
mutation updateUser($user: UserMutationInput!) {
    users {
        updateUser(user: $user) {
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


def test_graphql_update_user_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_update_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user1",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["updateUser"]["code"] == 200
    assert response.json()["data"]["users"]["updateUser"]["message"] is not None
    assert response.json()["data"]["users"]["updateUser"]["success"] is True

    assert response.json()["data"]["users"]["updateUser"]["user"]["username"] == "user1"
    assert response.json()["data"]["users"]["updateUser"]["user"]["sshKeys"] == [
        "ssh-rsa KEY user1@pc"
    ]
    assert mock_subprocess_popen.call_count == 1


def test_graphql_update_nonexistent_user(
    authorized_client, some_users, mock_subprocess_popen
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UPDATE_USER_MUTATION,
            "variables": {
                "user": {
                    "username": "user666",
                    "password": "12345678",
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["users"]["updateUser"]["code"] == 404
    assert response.json()["data"]["users"]["updateUser"]["message"] is not None
    assert response.json()["data"]["users"]["updateUser"]["success"] is False

    assert response.json()["data"]["users"]["updateUser"]["user"] is None
    assert mock_subprocess_popen.call_count == 1
