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


def test_delete_just_delete(authorized_client, some_users, mock_subprocess_popen):
    response = authorized_client.delete("/users")
    assert response.status_code == 405
