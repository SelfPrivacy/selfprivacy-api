# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import json
import os
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
    """Mock subprocess.Popen for broken service"""

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
    mock = mocker.patch(
        "selfprivacy_api.utils.network.get_ip4",
        autospec=True,
        return_value="157.90.247.192",
    )
    return mock


@pytest.fixture
def mock_get_ip6(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.network.get_ip6",
        autospec=True,
        return_value="fe80::9400:ff:fef1:34ae",
    )
    return mock


@pytest.fixture
def mock_dkim_key(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.get_dkim_key",
        autospec=True,
        return_value="I am a DKIM key",
    )


API_PYTHON_VERSION_INFO = """
info {
    pythonVersion
}
"""


def test_graphql_get_python_version_wrong_auth(
    wrong_auth_client, mock_subprocess_check_output
):
    """Test wrong auth"""
    response = wrong_auth_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_PYTHON_VERSION_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None


def test_graphql_get_python_version(authorized_client, mock_subprocess_check_output):
    """Test get python version"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_PYTHON_VERSION_INFO]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["system"]["info"]["pythonVersion"] == "Testing Linux"
    assert mock_subprocess_check_output.call_count == 1
    assert mock_subprocess_check_output.call_args[0][0] == ["python", "-V"]


API_SYSTEM_VERSION_INFO = """
info {
    systemVersion
}
"""


def test_graphql_get_system_version_unauthorized(
    wrong_auth_client, mock_subprocess_check_output
):
    """Test wrong auth"""
    response = wrong_auth_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_SYSTEM_VERSION_INFO]),
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is None

    assert mock_subprocess_check_output.call_count == 0


def test_graphql_get_system_version(authorized_client, mock_subprocess_check_output):
    """Test get system version"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_SYSTEM_VERSION_INFO]),
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is not None

    assert response.json["data"]["sytem"]["info"]["systemVersion"] == "Testing Linux"
    assert mock_subprocess_check_output.call_count == 1
    assert mock_subprocess_check_output.call_args[0][0] == ["uname", "-a"]


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


def is_dns_record_in_array(records, dns_record) -> bool:
    for record in records:
        if (
            record["type"] == dns_record["type"]
            and record["name"] == dns_record["name"]
            and record["content"] == dns_record["content"]
            and record["ttl"] == dns_record["ttl"]
            and record["priority"] == dns_record["priority"]
        ):
            return True
    return False


def test_graphql_get_domain(
    authorized_client, domain_file, mock_get_ip4, mock_get_ip6, turned_on
):
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
    dns_records = response.json["data"]["system"]["domainInfo"]["requiredDnsRecords"]
    assert is_dns_record_in_array(dns_records, dns_record())
    assert is_dns_record_in_array(dns_records, dns_record(type="AAAA"))
    assert is_dns_record_in_array(dns_records, dns_record(name="api.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="api.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="cloud.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="cloud.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="git.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="git.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="meet.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="meet.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="password.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="password.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="social.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="social.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(dns_records, dns_record(name="vpn.test.tld"))
    assert is_dns_record_in_array(
        dns_records, dns_record(name="vpn.test.tld", type="AAAA")
    )
    assert is_dns_record_in_array(
        dns_records,
        dns_record(name="test.tld", type="MX", content="test.tld", priority=10),
    )
    assert is_dns_record_in_array(
        dns_records,
        dns_record(
            name="_dmarc.test.tld", type="TXT", content="v=DMARC1; p=none", ttl=18000
        ),
    )
    assert is_dns_record_in_array(
        dns_records,
        dns_record(
            name="test.tld",
            type="TXT",
            content="v=spf1 a mx ip4:157.90.247.192 -all",
            ttl=18000,
        ),
    )
    assert is_dns_record_in_array(
        dns_records,
        dns_record(
            name="selector._domainkey.test.tld",
            type="TXT",
            content="I am a DKIM key",
            ttl=18000,
        ),
    )


API_GET_TIMEZONE = """
settings {
    timezone
}
"""


def test_graphql_get_timezone_unauthorized(client, turned_on):
    """Test get timezone without auth"""
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


def test_graphql_get_timezone_on_undefined(authorized_client, undefined_config):
    """Test get timezone when none is defined in config"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": generate_system_query([API_GET_TIMEZONE]),
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["system"]["settings"]["timezone"] == "Europe/Uzhgorod"


API_CHANGE_TIMEZONE_MUTATION = """
mutation changeTimezone($timezone: String!) {
    changeTimezone(timezone: $timezone) {
        success
        message
        code
        timezone
    }
}
"""


def test_graphql_change_timezone_unauthorized(client, turned_on):
    """Test change timezone without auth"""
    response = client.post(
        "/graphql",
        json={
            "query": API_CHANGE_TIMEZONE_MUTATION,
            "variables": {
                "timezone": "Europe/Moscow",
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None


def test_graphql_change_timezone(authorized_client, turned_on):
    """Test change timezone"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_TIMEZONE_MUTATION,
            "variables": {
                "timezone": "Europe/Helsinki",
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeTimezone"]["success"] is True
    assert response.json["data"]["changeTimezone"]["message"] is not None
    assert response.json["data"]["changeTimezone"]["code"] == 200
    assert response.json["data"]["changeTimezone"]["timezone"] == "Europe/Helsinki"
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Helsinki"


def test_graphql_change_timezone_on_undefined(authorized_client, undefined_config):
    """Test change timezone when none is defined in config"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_TIMEZONE_MUTATION,
            "variables": {
                "timezone": "Europe/Helsinki",
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeTimezone"]["success"] is True
    assert response.json["data"]["changeTimezone"]["message"] is not None
    assert response.json["data"]["changeTimezone"]["code"] == 200
    assert response.json["data"]["changeTimezone"]["timezone"] == "Europe/Helsinki"
    assert (
        read_json(undefined_config / "undefined.json")["timezone"] == "Europe/Helsinki"
    )


def test_graphql_change_timezone_without_timezone(authorized_client, turned_on):
    """Test change timezone without timezone"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_TIMEZONE_MUTATION,
            "variables": {
                "timezone": "",
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeTimezone"]["success"] is False
    assert response.json["data"]["changeTimezone"]["message"] is not None
    assert response.json["data"]["changeTimezone"]["code"] == 400
    assert response.json["data"]["changeTimezone"]["timezone"] is None
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Moscow"


def test_graphql_change_timezone_with_invalid_timezone(authorized_client, turned_on):
    """Test change timezone with invalid timezone"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_TIMEZONE_MUTATION,
            "variables": {
                "timezone": "Invlaid/Timezone",
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeTimezone"]["success"] is False
    assert response.json["data"]["changeTimezone"]["message"] is not None
    assert response.json["data"]["changeTimezone"]["code"] == 400
    assert response.json["data"]["changeTimezone"]["timezone"] is None
    assert read_json(turned_on / "turned_on.json")["timezone"] == "Europe/Moscow"


API_GET_AUTO_UPGRADE_SETTINGS_QUERY = """
settings {
    autoUpgrade {
        enableAutoUpgrade
        allowReboot
    }
}
"""


def test_graphql_get_auto_upgrade_unauthorized(client, turned_on):
    """Test get auto upgrade settings without auth"""
    response = client.get(
        "/graphql",
        json={
            "query": API_GET_AUTO_UPGRADE_SETTINGS_QUERY,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None


def test_graphql_get_auto_upgrade(authorized_client, turned_on):
    """Test get auto upgrade settings"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": API_GET_AUTO_UPGRADE_SETTINGS_QUERY,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["settings"]["autoUpgrade"]["enableAutoUpgrade"] is True
    assert response.json["data"]["settings"]["autoUpgrade"]["allowReboot"] is True


def test_graphql_get_auto_upgrade_on_undefined(authorized_client, undefined_config):
    """Test get auto upgrade settings when none is defined in config"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": API_GET_AUTO_UPGRADE_SETTINGS_QUERY,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["settings"]["autoUpgrade"]["enableAutoUpgrade"] is True
    assert response.json["data"]["settings"]["autoUpgrade"]["allowReboot"] is False


def test_graphql_get_auto_upgrade_without_vlaues(authorized_client, no_values):
    """Test get auto upgrade settings without values"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": API_GET_AUTO_UPGRADE_SETTINGS_QUERY,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["settings"]["autoUpgrade"]["enableAutoUpgrade"] is True
    assert response.json["data"]["settings"]["autoUpgrade"]["allowReboot"] is False


def test_graphql_get_auto_upgrade_turned_off(authorized_client, turned_off):
    """Test get auto upgrade settings when turned off"""
    response = authorized_client.get(
        "/graphql",
        json={
            "query": API_GET_AUTO_UPGRADE_SETTINGS_QUERY,
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert (
        response.json["data"]["settings"]["autoUpgrade"]["enableAutoUpgrade"] is False
    )
    assert response.json["data"]["settings"]["autoUpgrade"]["allowReboot"] is False


API_CHANGE_AUTO_UPGRADE_SETTINGS = """
mutation changeServerSettings($settings: AutoUpgradeSettingsInput!) {
    changeAutoUpgradeSettings(settings: $settings) {
        success
        message
        code
        enableAutoUpgrade
        allowReboot
    }
}
"""


def test_graphql_change_auto_upgrade_unauthorized(client, turned_on):
    """Test change auto upgrade settings without auth"""
    response = client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": True,
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None


def test_graphql_change_auto_upgrade(authorized_client, turned_on):
    """Test change auto upgrade settings"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": False,
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is False
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is True
    assert read_json(turned_on / "turned_on.json")["autoUpgrade"]["enable"] is False
    assert read_json(turned_on / "turned_on.json")["autoUpgrade"]["allowReboot"] is True


def test_graphql_change_auto_upgrade_on_undefined(authorized_client, undefined_config):
    """Test change auto upgrade settings when none is defined in config"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": False,
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is False
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is True
    assert (
        read_json(undefined_config / "undefined.json")["autoUpgrade"]["enable"] is False
    )
    assert (
        read_json(undefined_config / "undefined.json")["autoUpgrade"]["allowReboot"]
        is True
    )


def test_graphql_change_auto_upgrade_without_vlaues(authorized_client, no_values):
    """Test change auto upgrade settings without values"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": True,
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is True
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is True
    assert read_json(no_values / "no_values.json")["autoUpgrade"]["enable"] is True
    assert read_json(no_values / "no_values.json")["autoUpgrade"]["allowReboot"] is True


def test_graphql_change_auto_upgrade_turned_off(authorized_client, turned_off):
    """Test change auto upgrade settings when turned off"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": True,
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is True
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is True
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"]["enable"] is True
    assert (
        read_json(turned_off / "turned_off.json")["autoUpgrade"]["allowReboot"] is True
    )


def test_grphql_change_auto_upgrade_without_enable(authorized_client, turned_off):
    """Test change auto upgrade settings without enable"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "allowReboot": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is False
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is True
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"]["enable"] is False
    assert (
        read_json(turned_off / "turned_off.json")["autoUpgrade"]["allowReboot"] is True
    )


def test_graphql_change_auto_upgrade_without_allow_reboot(
    authorized_client, turned_off
):
    """Test change auto upgrade settings without allow reboot"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {
                    "enableAutoUpgrade": True,
                },
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is True
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is False
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"]["enable"] is True
    assert (
        read_json(turned_off / "turned_off.json")["autoUpgrade"]["allowReboot"] is False
    )


def test_graphql_change_auto_upgrade_with_empty_input(authorized_client, turned_off):
    """Test change auto upgrade settings with empty input"""
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_CHANGE_AUTO_UPGRADE_SETTINGS,
            "variables": {
                "settings": {},
            },
        },
    )
    assert response.status_code == 200
    assert response.json.get("data") is None
    assert response.json["data"]["changeAutoUpgradeSettings"]["success"] is True
    assert response.json["data"]["changeAutoUpgradeSettings"]["message"] is not None
    assert response.json["data"]["changeAutoUpgradeSettings"]["code"] == 200
    assert (
        response.json["data"]["changeAutoUpgradeSettings"]["enableAutoUpgrade"] is False
    )
    assert response.json["data"]["changeAutoUpgradeSettings"]["allowReboot"] is False
    assert read_json(turned_off / "turned_off.json")["autoUpgrade"]["enable"] is False
    assert (
        read_json(turned_off / "turned_off.json")["autoUpgrade"]["allowReboot"] is False
    )


API_PULL_SYSTEM_CONFIGURATION_MUTATION = """
mutation testPullSystemConfiguration() {
    pullRepositoryChanges {
        success
        message
        code
    }
}
"""


def test_graphql_pull_system_configuration_unauthorized(client, mock_subprocess_popen):
    response = client.post(
        "/graphql",
        json={
            "query": API_PULL_SYSTEM_CONFIGURATION_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is None
    assert mock_subprocess_popen.call_count == 0


def test_graphql_pull_system_configuration(
    authorized_client, mock_subprocess_popen, mock_os_chdir
):
    current_dir = os.getcwd()
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_PULL_SYSTEM_CONFIGURATION_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["pullRepositoryChanges"]["success"] is True
    assert response.json["data"]["pullRepositoryChanges"]["message"] is not None
    assert response.json["data"]["pullRepositoryChanges"]["code"] == 200

    assert mock_subprocess_popen.call_count == 1
    assert mock_subprocess_popen.call_args[0][0] == ["git", "pull"]
    assert mock_os_chdir.call_count == 2
    assert mock_os_chdir.call_args_list[0][0][0] == "/etc/nixos"
    assert mock_os_chdir.call_args_list[1][0][0] == current_dir


def test_graphql_pull_system_broken_repo(
    authorized_client, mock_broken_service, mock_os_chdir
):
    current_dir = os.getcwd()

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_PULL_SYSTEM_CONFIGURATION_MUTATION,
        },
    )

    assert response.status_code == 200
    assert response.json.get("data") is not None
    assert response.json["data"]["pullRepositoryChanges"]["success"] is False
    assert response.json["data"]["pullRepositoryChanges"]["message"] is not None
    assert response.json["data"]["pullRepositoryChanges"]["code"] == 500

    assert mock_broken_service.call_count == 1
    assert mock_os_chdir.call_count == 2
    assert mock_os_chdir.call_args_list[0][0][0] == "/etc/nixos"
    assert mock_os_chdir.call_args_list[1][0][0] == current_dir
