import base64
import json
import pytest


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


###############################################################################


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (b"I am a DKIM key", None)


class NoFileMock(ProcessMock):
    def communicate():
        return (b"", None)


@pytest.fixture
def mock_subproccess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    mocker.patch(
        "selfprivacy_api.resources.services.mailserver.get_domain",
        autospec=True,
        return_value="example.com",
    )
    mocker.patch("os.path.exists", autospec=True, return_value=True)
    return mock


@pytest.fixture
def mock_no_file(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=NoFileMock)
    mocker.patch(
        "selfprivacy_api.resources.services.mailserver.get_domain",
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


def test_dkim_key(authorized_client, mock_subproccess_popen):
    """Test DKIM key"""
    response = authorized_client.get("/services/mailserver/dkim")
    assert response.status_code == 200
    assert base64.b64decode(response.data) == b"I am a DKIM key"
    assert mock_subproccess_popen.call_args[0][0] == [
        "cat",
        "/var/dkim/example.com.selector.txt",
    ]


def test_no_dkim_key(authorized_client, mock_no_file):
    """Test no DKIM key"""
    response = authorized_client.get("/services/mailserver/dkim")
    assert response.status_code == 404
    assert mock_no_file.called == False
