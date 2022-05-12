# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


invalid_usernames = [
    "root",
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

    def communicate():
        return (b"NEW_HASHED", None)

    returncode = 0


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


##  TESTS  ######################################################


def test_get_users_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.get("/users")
    assert response.status_code == 401


def test_get_some_users(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.get("/users")
    assert response.status_code == 200
    assert response.json == ["user1", "user2", "user3"]


def test_get_one_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.get("/users")
    assert response.status_code == 200
    assert response.json == ["user1"]


def test_get_one_user_with_main(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.get("/users?withMainUser=true")
    assert response.status_code == 200
    assert response.json == ["tester", "user1"]


def test_get_no_users(authorized_client, no_users, mock_subprocess_popen):
    response = authorized_client.get("/users")
    assert response.status_code == 200
    assert response.json == []


def test_get_no_users_with_main(authorized_client, no_users, mock_subprocess_popen):
    response = authorized_client.get("/users?withMainUser=true")
    assert response.status_code == 200
    assert response.json == ["tester"]


def test_get_undefined_users(
    authorized_client, undefined_settings, mock_subprocess_popen
):
    response = authorized_client.get("/users")
    assert response.status_code == 200
    assert response.json == []


def test_post_users_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.post("/users")
    assert response.status_code == 401


def test_post_one_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/users", json={"username": "user4", "password": "password"}
    )
    assert response.status_code == 201
    assert read_json(one_user / "one_user.json")["users"] == [
        {
            "username": "user1",
            "hashedPassword": "HASHED_PASSWORD_1",
            "sshKeys": ["ssh-rsa KEY user1@pc"],
        },
        {
            "username": "user4",
            "hashedPassword": "NEW_HASHED",
        },
    ]


def test_post_without_username(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post("/users", json={"password": "password"})
    assert response.status_code == 400


def test_post_without_password(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post("/users", json={"username": "user4"})
    assert response.status_code == 400


def test_post_without_username_and_password(
    authorized_client, one_user, mock_subprocess_popen
):
    response = authorized_client.post("/users", json={})
    assert response.status_code == 400


@pytest.mark.parametrize("username", invalid_usernames)
def test_post_system_user(authorized_client, one_user, mock_subprocess_popen, username):
    response = authorized_client.post(
        "/users", json={"username": username, "password": "password"}
    )
    assert response.status_code == 409


def test_post_existing_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/users", json={"username": "user1", "password": "password"}
    )
    assert response.status_code == 409


def test_post_existing_main_user(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/users", json={"username": "tester", "password": "password"}
    )
    assert response.status_code == 409


def test_post_user_to_undefined_users(
    authorized_client, undefined_settings, mock_subprocess_popen
):
    response = authorized_client.post(
        "/users", json={"username": "user4", "password": "password"}
    )
    assert response.status_code == 201
    assert read_json(undefined_settings / "undefined.json")["users"] == [
        {"username": "user4", "hashedPassword": "NEW_HASHED"}
    ]


def test_post_very_long_username(authorized_client, one_user, mock_subprocess_popen):
    response = authorized_client.post(
        "/users", json={"username": "a" * 32, "password": "password"}
    )
    assert response.status_code == 400


@pytest.mark.parametrize("username", ["", "1", "фыр", "user1@", "№:%##$^&@$&^()_"])
def test_post_invalid_username(
    authorized_client, one_user, mock_subprocess_popen, username
):
    response = authorized_client.post(
        "/users", json={"username": username, "password": "password"}
    )
    assert response.status_code == 400


def test_delete_user_unauthorized(client, some_users, mock_subprocess_popen):
    response = client.delete("/users/user1")
    assert response.status_code == 401


def test_delete_user_not_found(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users/user4")
    assert response.status_code == 404


def test_delete_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users/user1")
    assert response.status_code == 200
    assert read_json(some_users / "some_users.json")["users"] == [
        {"username": "user2", "hashedPassword": "HASHED_PASSWORD_2", "sshKeys": []},
        {"username": "user3", "hashedPassword": "HASHED_PASSWORD_3"},
    ]


@pytest.mark.parametrize("username", invalid_usernames)
def test_delete_system_user(
    authorized_client, some_users, mock_subprocess_popen, username
):
    response = authorized_client.delete("/users/" + username)
    assert response.status_code == 400 or response.status_code == 404


def test_delete_main_user(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users/tester")
    assert response.status_code == 400


def test_delete_without_argument(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users/")
    assert response.status_code == 404


def test_delete_just_delete(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users")
    assert response.status_code == 405
