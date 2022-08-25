import base64
import json
import pytest


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def call_args_asserts(mocked_object):
    assert mocked_object.call_count == 7
    assert mocked_object.call_args_list[0][0][0] == [
        "systemctl",
        "show",
        "dovecot2.service",
    ]
    assert mocked_object.call_args_list[1][0][0] == [
        "systemctl",
        "show",
        "postfix.service",
    ]
    assert mocked_object.call_args_list[2][0][0] == [
        "systemctl",
        "show",
        "vaultwarden.service",
    ]
    assert mocked_object.call_args_list[3][0][0] == [
        "systemctl",
        "show",
        "gitea.service",
    ]
    assert mocked_object.call_args_list[4][0][0] == [
        "systemctl",
        "show",
        "phpfpm-nextcloud.service",
    ]
    assert mocked_object.call_args_list[5][0][0] == [
        "systemctl",
        "show",
        "ocserv.service",
    ]
    assert mocked_object.call_args_list[6][0][0] == [
        "systemctl",
        "show",
        "pleroma.service",
    ]


SUCCESSFUL_STATUS = b"""
Type=oneshot
ExitType=main
Restart=no
NotifyAccess=none
RestartUSec=100ms
LoadState=loaded
ActiveState=active
FreezerState=running
SubState=exited
"""

FAILED_STATUS = b"""
Type=oneshot
ExitType=main
Restart=no
NotifyAccess=none
RestartUSec=100ms
LoadState=loaded
ActiveState=failed
FreezerState=running
SubState=exited
"""


@pytest.fixture
def mock_subproccess_popen(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=SUCCESSFUL_STATUS
    )
    return mock


@pytest.fixture
def mock_broken_service(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=FAILED_STATUS
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
    assert response.json() == {
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
    assert response.json() == {
        "imap": 1,
        "smtp": 1,
        "http": 0,
        "bitwarden": 1,
        "gitea": 1,
        "nextcloud": 1,
        "ocserv": 1,
        "pleroma": 1,
    }
    call_args_asserts(mock_broken_service)
