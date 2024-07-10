import pytest

from selfprivacy_api.services.service import ServiceStatus
from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.forgejo import Forgejo
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.nextcloud import Nextcloud
from selfprivacy_api.services.ocserv import Ocserv
from selfprivacy_api.services.pleroma import Pleroma


def expected_status_call(service_name: str):
    return ["systemctl", "show", service_name]


def call_args_asserts(mocked_object):
    assert mocked_object.call_count == 7
    calls = [callargs[0][0] for callargs in mocked_object.call_args_list]
    assert calls == [
        expected_status_call(service)
        for service in [
            "dovecot2.service",
            "postfix.service",
            "vaultwarden.service",
            "forgejo.service",
            "phpfpm-nextcloud.service",
            "ocserv.service",
            "pleroma.service",
        ]
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
def mock_popen_systemctl_service_ok(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=SUCCESSFUL_STATUS
    )
    return mock


@pytest.fixture
def mock_popen_systemctl_service_not_ok(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=FAILED_STATUS
    )
    return mock


###############################################################################


def test_systemctl_ok(mock_popen_systemctl_service_ok):
    assert MailServer.get_status() == ServiceStatus.ACTIVE
    assert Bitwarden.get_status() == ServiceStatus.ACTIVE
    assert Forgejo.get_status() == ServiceStatus.ACTIVE
    assert Nextcloud.get_status() == ServiceStatus.ACTIVE
    assert Ocserv.get_status() == ServiceStatus.ACTIVE
    assert Pleroma.get_status() == ServiceStatus.ACTIVE
    call_args_asserts(mock_popen_systemctl_service_ok)


def test_systemctl_failed_service(mock_popen_systemctl_service_not_ok):
    assert MailServer.get_status() == ServiceStatus.FAILED
    assert Bitwarden.get_status() == ServiceStatus.FAILED
    assert Forgejo.get_status() == ServiceStatus.FAILED
    assert Nextcloud.get_status() == ServiceStatus.FAILED
    assert Ocserv.get_status() == ServiceStatus.FAILED
    assert Pleroma.get_status() == ServiceStatus.FAILED
    call_args_asserts(mock_popen_systemctl_service_not_ok)
