import pytest

from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.gitea import Gitea
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.ocserv import Ocserv
from selfprivacy_api.services.pleroma import Pleroma


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

def test_dkim_key(authorized_client, mock_subproccess_popen):
    assert MailServer.get_status() == ServiceStatus.ACTIVE 
    assert Bitwarden.get_status() == ServiceStatus.ACTIVE
    assert Gitea.get_status() == ServiceStatus.ACTIVE
    assert Nextcloud.get_status() == ServiceStatus.ACTIVE
    assert Ocserv.get_status() == ServiceStatus.ACTIVE
    assert Pleroma.get_status() == ServiceStatus.ACTIVE
    call_args_asserts(mock_subproccess_popen)


def test_no_dkim_key(authorized_client, mock_broken_service):
    assert MailServer.get_status() == ServiceStatus.FAILED 
    assert Bitwarden.get_status() == ServiceStatus.FAILED
    assert Gitea.get_status() == ServiceStatus.FAILED
    assert Nextcloud.get_status() == ServiceStatus.FAILED
    assert Ocserv.get_status() == ServiceStatus.FAILED
    assert Pleroma.get_status() == ServiceStatus.FAILED
    call_args_asserts(mock_broken_service)
