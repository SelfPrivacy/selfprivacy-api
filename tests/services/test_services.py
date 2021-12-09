import base64
import json
import pytest


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_args_asserts(mocked_object):
    assert mocked_object.call_count == 8
    assert mocked_object.call_args_list[0][0][0] == [
        "systemctl",
        "status",
        "dovecot2.service",
    ]
    assert mocked_object.call_args_list[1][0][0] == [
        "systemctl",
        "status",
        "postfix.service",
    ]
    assert mocked_object.call_args_list[2][0][0] == [
        "systemctl",
        "status",
        "nginx.service",
    ]
    assert mocked_object.call_args_list[3][0][0] == [
        "systemctl",
        "status",
        "bitwarden_rs.service",
    ]
    assert mocked_object.call_args_list[4][0][0] == [
        "systemctl",
        "status",
        "gitea.service",
    ]
    assert mocked_object.call_args_list[5][0][0] == [
        "systemctl",
        "status",
        "phpfpm-nextcloud.service",
    ]
    assert mocked_object.call_args_list[6][0][0] == [
        "systemctl",
        "status",
        "ocserv.service",
    ]
    assert mocked_object.call_args_list[7][0][0] == [
        "systemctl",
        "status",
        "pleroma.service",
    ]


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (b"", None)

    returncode = 0


class BrokenServiceMock(ProcessMock):
    returncode = 3


@pytest.fixture
def mock_subproccess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_broken_service(mocker):
    mock = mocker.patch(
        "subprocess.Popen", autospec=True, return_value=BrokenServiceMock
    )
    return mock


###############################################################################


def test_unauthorized(client, mock_subproccess_popen):
    """Test unauthorized"""
    response = client.get("/services/status")
    assert response.status_code == 401


def test_illegal_methods(authorized_client, mock_subproccess_popen):
    response = authorized_client.post("/services/status")
    assert response.status_code == 405
    response = authorized_client.put("/services/status")
    assert response.status_code == 405
    response = authorized_client.delete("/services/status")
    assert response.status_code == 405


def test_dkim_key(authorized_client, mock_subproccess_popen):
    response = authorized_client.get("/services/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "imap": 0,
        "smtp": 0,
        "http": 0,
        "bitwarden": 0,
        "gitea": 0,
        "nextcloud": 0,
        "ocserv": 0,
        "pleroma": 0,
    }
    call_args_asserts(mock_subproccess_popen)


def test_no_dkim_key(authorized_client, mock_broken_service):
    response = authorized_client.get("/services/status")
    assert response.status_code == 200
    assert response.get_json() == {
        "imap": 3,
        "smtp": 3,
        "http": 3,
        "bitwarden": 3,
        "gitea": 3,
        "nextcloud": 3,
        "ocserv": 3,
        "pleroma": 3,
    }
    call_args_asserts(mock_broken_service)
