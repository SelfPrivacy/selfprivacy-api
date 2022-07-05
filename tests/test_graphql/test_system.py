# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import json
import pytest
import datetime

from tests.common import generate_system_query, read_json, write_json

@pytest.fixture
def domain_file(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.DOMAIN_FILE", datadir / "domain")
    return datadir


@pytest.fixture
def turned_on(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_on.json")
    assert read_json(datadir / "turned_on.json")["autoUpgrade"]["enable"] == True
    assert read_json(datadir / "turned_on.json")["autoUpgrade"]["allowReboot"] == True
    assert read_json(datadir / "turned_on.json")["timezone"] == "Europe/Moscow"
    return datadir


@pytest.fixture
def turned_off(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "turned_off.json")
    assert read_json(datadir / "turned_off.json")["autoUpgrade"]["enable"] == False
    assert read_json(datadir / "turned_off.json")["autoUpgrade"]["allowReboot"] == False
    assert read_json(datadir / "turned_off.json")["timezone"] == "Europe/Moscow"
    return datadir


@pytest.fixture
def undefined_config(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "undefined.json")
    assert "autoUpgrade" not in read_json(datadir / "undefined.json")
    assert "timezone" not in read_json(datadir / "undefined.json")
    return datadir


@pytest.fixture
def no_values(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "no_values.json")
    assert "enable" not in read_json(datadir / "no_values.json")["autoUpgrade"]
    assert "allowReboot" not in read_json(datadir / "no_values.json")["autoUpgrade"]
    return datadir


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():
        return (b"", None)

    returncode = 0


class BrokenServiceMock(ProcessMock):
    def communicate():
        return (b"Testing error", None)

    returncode = 3


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


@pytest.fixture
def mock_os_chdir(mocker):
    mock = mocker.patch("os.chdir", autospec=True)
    return mock


@pytest.fixture
def mock_broken_service(mocker):
    mock = mocker.patch(
        "subprocess.Popen", autospec=True, return_value=BrokenServiceMock
    )
    return mock


@pytest.fixture
def mock_subprocess_check_output(mocker):
    mock = mocker.patch(
        "subprocess.check_output", autospec=True, return_value=b"Testing Linux"
    )
    return mock

@pytest.fixture
def mock_get_ip4(mocker):
    mock = mocker.patch("selfprivacy_api.utils.network.get_ip4", autospec=True, return_value="157.90.247.192")
    return mock

@pytest.fixture
def mock_get_ip6(mocker):
    mock = mocker.patch("selfprivacy_api.utils.network.get_ip6", autospec=True, return_value="fe80::9400:ff:fef1:34ae")
    return mock

@pytest.fixture
def mock_dkim_key(mocker):
    mock = mocker.patch("selfprivacy_api.utils.get_dkim_key", autospec=True, return_value="I am a DKIM key")

API_PYTHON_VERSION_INFO = """
info {
    pythonVersion
}
"""


def test_graphql_wrong_auth(wrong_auth_client):
    """Test wrong auth"""
    response = wrong_auth_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_PYTHON_VERSION_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None

API_GET_DOMAIN_INFO = """
domainInfo {
    domain
    hostname
    provider
    requiredDnsRecords {
        type
        name
        content
        ttl
        priority
    }
}
"""

def dns_record(type="A", name="test.tld", content=None, ttl=3600, priority=None):
    if content is None:
        if type == "A":
            content = "157.90.247.192"
        elif type == "AAAA":
            content = "fe80::9400:ff:fef1:34ae"
    return {
        "type": type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "priority": priority,
    }

def test_graphql_get_domain(authorized_client, domain_file, mock_get_ip4, mock_get_ip6, turned_on):
    """Test get domain"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_GET_DOMAIN_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["system"]["domainInfo"]["domain"] == "test.tld"
    assert response.json["data"]["system"]["domainInfo"]["hostname"] == "test-instance"
    assert response.json["data"]["system"]["domainInfo"]["provider"] == "HETZNER"
    assert response.json["data"]["system"]["domainInfo"]["requiredDnsRecords"] == [
        dns_record(),
        dns_record(type="AAAA"),
        dns_record(name="api.test.tld"),
        dns_record(name="api.test.tld", type="AAAA"),
        dns_record(name="cloud.test.tld"),
        dns_record(name="cloud.test.tld", type="AAAA"),
        dns_record(name="git.test.tld"),
        dns_record(name="git.test.tld", type="AAAA"),
        dns_record(name="meet.test.tld"),
        dns_record(name="meet.test.tld", type="AAAA"),
        dns_record(name="password.test.tld"),
        dns_record(name="password.test.tld", type="AAAA"),
        dns_record(name="social.test.tld"),
        dns_record(name="social.test.tld", type="AAAA"),
        dns_record(name="vpn.test.tld"),
        dns_record(name="vpn.test.tld", type="AAAA"),
        dns_record(name="test.tld", type="MX", content="test.tld", priority=10),
        dns_record(name="_dmarc.test.tld", type="TXT", content="v=DMARC1; p=none", ttl=18000),
        dns_record(name="test.tld", type="TXT", content="v=spf1 a mx ip4:157.90.247.192 -all", ttl=18000),
        dns_record(name="selector._domainkey.test.tld", type="TXT", content="I am a DKIM key", ttl=18000),
    ]

API_GET_TIMEZONE = """
settings {
    timezone
}
"""

def test_graphql_get_timezone_unauthorized(client, turned_on):
    """Test get timezone"""
    response = client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_GET_TIMEZONE]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None

def test_graphql_get_timezone(authorized_client, turned_on):
    """Test get timezone"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_GET_TIMEZONE]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["system"]["settings"]["timezone"] == "Europe/Moscow"

API_GET_PYTHON_VERSION = """
info {
    pythonVersion
}
"""
