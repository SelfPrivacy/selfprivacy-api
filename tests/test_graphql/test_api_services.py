# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import pytest

from tests.common import read_json


class NextcloudMockReturnTrue:
    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def enable():
        pass

    def disable():
        pass

    def stop():
        pass

    def is_movable():
        return True

    def move_to_volume(what):
        return None

    def start():
        pass

    def restart():
        pass

    returncode = 0


class BlockDevices:
    def get_block_device(location):
        return True


class ProcessMock:
    """Mock subprocess.Popen"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def communicate():  # pylint: disable=no-method-argument
        return (b"", None)

    returncode = 0


@pytest.fixture
def mock_subprocess_popen(mocker):
    mock = mocker.patch("subprocess.Popen", autospec=True, return_value=ProcessMock)
    return mock


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
def mock_service_to_graphql_service(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.services_mutations.service_to_graphql_service",
        autospec=True,
        return_value=None,
    )
    return mock


@pytest.fixture
def mock_job_to_api_job(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.services_mutations.job_to_api_job",
        autospec=True,
        return_value=None,
    )
    return mock


@pytest.fixture
def mock_block_devices_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevices",
        autospec=True,
        return_value=None,
    )
    return mock


@pytest.fixture
def mock_block_devices(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.services_mutations.BlockDevices",
        autospec=True,
        return_value=BlockDevices,
    )
    return mock


@pytest.fixture
def mock_get_service_by_id_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.services_mutations.get_service_by_id",
        autospec=True,
        return_value=None,
    )
    return mock


@pytest.fixture
def mock_get_service_by_id(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.services_mutations.get_service_by_id",
        autospec=True,
        return_value=NextcloudMockReturnTrue,
    )
    return mock


####################################################################


API_ENABLE_SERVICE_MUTATION = """
mutation enableService($serviceId: String!) {
    enableService(serviceId: $serviceId) {
        success
        message
        code
    }
}
"""


def test_graphql_enable_service_unauthorized_client(
    client, mock_get_service_by_id_return_none, mock_subprocess_popen
):
    response = client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_enable_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_subprocess_popen,
    one_user,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["enableService"]["code"] == 404
    assert response.json()["data"]["enableService"]["message"] is not None
    assert response.json()["data"]["enableService"]["success"] is False


def test_graphql_enable_service(
    authorized_client,
    mock_get_service_by_id,
    mock_subprocess_popen,
    one_user,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["enableService"]["code"] == 200
    assert response.json()["data"]["enableService"]["message"] is not None
    assert response.json()["data"]["enableService"]["success"] is True


API_DISABLE_SERVICE_MUTATION = """
mutation disableService($serviceId: String!) {
    disableService(serviceId: $serviceId) {
        success
        message
        code
    }
}
"""


def test_graphql_disable_service_unauthorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_subprocess_popen,
    one_user,
    mock_service_to_graphql_service,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_disable_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_subprocess_popen,
    one_user,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["disableService"]["code"] == 404
    assert response.json()["data"]["disableService"]["message"] is not None
    assert response.json()["data"]["disableService"]["success"] is False


def test_graphql_disable_services(
    authorized_client,
    mock_get_service_by_id,
    mock_subprocess_popen,
    one_user,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["disableService"]["code"] == 200
    assert response.json()["data"]["disableService"]["message"] is not None
    assert response.json()["data"]["disableService"]["success"] is True


API_STOP_SERVICE_MUTATION = """
mutation stopService($serviceId: String!) {
    stopService(serviceId: $serviceId) {
        success
        message
        code
    }
}
"""


def test_graphql_stop_service_unauthorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_stop_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["stopService"]["code"] == 404
    assert response.json()["data"]["stopService"]["message"] is not None
    assert response.json()["data"]["stopService"]["success"] is False


def test_graphql_stop_service(
    authorized_client,
    mock_get_service_by_id,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["stopService"]["code"] == 200
    assert response.json()["data"]["stopService"]["message"] is not None
    assert response.json()["data"]["stopService"]["success"] is True


API_START_SERVICE_MUTATION = """
mutation startService($serviceId: String!) {
    startService(serviceId: $serviceId) {
        success
        message
        code
    }
}
"""


def test_graphql_start_service_unauthorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_start_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["startService"]["code"] == 404
    assert response.json()["data"]["startService"]["message"] is not None
    assert response.json()["data"]["startService"]["success"] is False


def test_graphql_start_service(
    authorized_client,
    mock_get_service_by_id,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["startService"]["code"] == 200
    assert response.json()["data"]["startService"]["message"] is not None
    assert response.json()["data"]["startService"]["success"] is True


API_RESTART_SERVICE_MUTATION = """
mutation restartService($serviceId: String!) {
    restartService(serviceId: $serviceId) {
        success
        message
        code
    }
}
"""


def test_graphql_restart_service_unauthorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_restart_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["restartService"]["code"] == 404
    assert response.json()["data"]["restartService"]["message"] is not None
    assert response.json()["data"]["restartService"]["success"] is False


def test_graphql_restart_service(
    authorized_client,
    mock_get_service_by_id,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"serviceId": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["restartService"]["code"] == 200
    assert response.json()["data"]["restartService"]["message"] is not None
    assert response.json()["data"]["restartService"]["success"] is True


API_MOVE_SERVICE_MUTATION = """
mutation moveService($input: MoveServiceInput!) {
    moveService(input: $input) {
        success
        message
        code
    }
}
"""


def test_graphql_move_service_unauthorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"serviceId": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_move_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"serviceId": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 404
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_not_movable_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"serviceId": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 404
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_service_volume_not_found(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_service_to_graphql_service,
    mock_block_devices_return_none,
    mock_subprocess_popen,
    one_user,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"serviceId": "nextcloud", "location": "sdx"},
            },
        },
    )

    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 404
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_service(
    authorized_client,
    mock_get_service_by_id,
    mock_service_to_graphql_service,
    mock_block_devices,
    mock_subprocess_popen,
    one_user,
    mock_job_to_api_job,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"serviceId": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 200
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is True
