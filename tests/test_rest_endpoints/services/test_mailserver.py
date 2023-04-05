import base64
import json
import pytest

from selfprivacy_api.utils import get_dkim_key

###############################################################################


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (
            b'selector._domainkey\tIN\tTXT\t( "v=DKIM1; k=rsa; "\n\t  "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB" )  ; ----- DKIM key selector for example.com\n',
            None,
        )


class NoFileMock(ProcessMock):
    def communicate():
        return (b"", None)


@pytest.fixture
def mock_subproccess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    mocker.patch(
        "selfprivacy_api.rest.services.get_domain",
        autospec=True,
        return_value="example.com",
    )
    mocker.patch("os.path.exists", autospec=True, return_value=True)
    return mock


@pytest.fixture
def mock_no_file(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=NoFileMock)
    mocker.patch(
        "selfprivacy_api.rest.services.get_domain",
        autospec=True,
        return_value="example.com",
    )
    mocker.patch("os.path.exists", autospec=True, return_value=False)
    return mock


###############################################################################


def test_unauthorized(client, mock_subproccess_popen):
    """Test unauthorized"""
    response = client.get("/services/mailserver/dkim")
    assert response.status_code == 401


def test_illegal_methods(authorized_client, mock_subproccess_popen):
    response = authorized_client.post("/services/mailserver/dkim")
    assert response.status_code == 405
    response = authorized_client.put("/services/mailserver/dkim")
    assert response.status_code == 405
    response = authorized_client.delete("/services/mailserver/dkim")
    assert response.status_code == 405


def test_get_dkim_key(mock_subproccess_popen):
    """Test DKIM key"""
    dkim_key = get_dkim_key("example.com")
    assert (
        dkim_key
        == "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB"
    )
    assert mock_subproccess_popen.call_args[0][0] == [
        "cat",
        "/var/dkim/example.com.selector.txt",
    ]


def test_dkim_key(authorized_client, mock_subproccess_popen):
    """Test old REST DKIM key endpoint"""
    response = authorized_client.get("/services/mailserver/dkim")
    assert response.status_code == 200
    assert (
        base64.b64decode(response.text)
        == b'selector._domainkey\tIN\tTXT\t( "v=DKIM1; k=rsa; "\n\t  "p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDNn/IhEz1SxgHxxxI8vlPYC2dNueiLe1GC4SYz8uHimC8SDkMvAwm7rqi2SimbFgGB5nccCNOqCkrIqJTCB9vufqBnVKAjshHqpOr5hk4JJ1T/AGQKWinstmDbfTLPYTbU8ijZrwwGeqQLlnXR5nSN0GB9GazheA9zaPsT6PV+aQIDAQAB" )  ; ----- DKIM key selector for example.com\n'
    )
    assert mock_subproccess_popen.call_args[0][0] == [
        "cat",
        "/var/dkim/example.com.selector.txt",
    ]


def test_no_dkim_key(authorized_client, mock_no_file):
    """Test no DKIM key"""
    response = authorized_client.get("/services/mailserver/dkim")
    assert response.status_code == 404
    assert mock_no_file.called == False
