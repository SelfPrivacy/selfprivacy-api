import pytest


def get_service_by_id_return_none_mock():
    return None


def get_service_by_id_mock():
    return "nextcloud"


def service_to_graphql_service_mock():
    pass


class BlockDevicesMock:
    def get_block_device(self, name: str):
        pass


class BlockDevicesReturnNoneMock:
    def get_block_device(self, name: str):
        return None


class NextcloudMock:
    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def enable(self):
        pass

    def disable(self):
        pass

    def stop(self):
        pass

    def is_movable(self):
        return True

    def move_to_volume(self):
        pass

    returncode = 0


class NextcloudReturnFalseMock:
    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def enable(self):
        pass

    def disable(self):
        pass

    def stop(self):
        pass

    def is_movable(self):
        return False

    def move_to_volume(self):
        pass

    returncode = 0


@pytest.fixture
def mock_service_to_graphql_service(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.common_types.service.service_to_graphql_service",
        autospec=True,
        return_value=service_to_graphql_service_mock,
    )
    return mock


@pytest.fixture
def mock_nextcloud(mocker):
    mock = mocker.patch(
        "selfprivacy_api.services.nextcloud.__init__.Nextcloud",
        autospec=True,
        return_value=NextcloudMock,
    )
    return mock


@pytest.fixture
def mock_block_devices_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevices",
        autospec=True,
        return_value=BlockDevicesReturnNoneMock,
    )
    return mock


@pytest.fixture
def mock_block_devices(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevices",
        autospec=True,
        return_value=BlockDevicesMock,
    )
    return mock


@pytest.fixture
def mock_nextcloud_return_false(mocker):
    mock = mocker.patch(
        "selfprivacy_api.services.nextcloud.__init__.Nextcloud",
        autospec=True,
        return_value=NextcloudReturnFalseMock,
    )
    return mock


@pytest.fixture
def mock_get_service_by_id_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.services.__init__.get_service_by_id",
        autospec=True,
        return_value=mock_get_service_by_id_return_none,
    )
    return mock


@pytest.fixture
def mock_get_service_by_id(mocker):
    mock = mocker.patch(
        "selfprivacy_api.services.__init__.get_service_by_id",
        autospec=True,
        return_value=mock_get_service_by_id,
    )
    return mock


####################################################################


API_ENABLE_SERVICE_MUTATION = """
mutation enableService($service_id: String!) {
    enableService(service_id: $service_id) {
        success
        message
        code
    }
}
"""


def test_graphql_enable_service_unathorized_client(
    client, mock_get_service_by_id_return_none, mock_nextcloud
):
    response = client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_enable_not_found_service(
    authorized_client, mock_get_service_by_id_return_none, mock_nextcloud
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["enableService"]["code"] == 404
    assert response.json()["data"]["enableService"]["message"] is not None
    assert response.json()["data"]["enableService"]["success"] is False


def test_graphql_enable_service(
    authorized_client, mock_get_service_by_id, mock_nextcloud
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_ENABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["enableService"]["code"] == 200
    assert response.json()["data"]["enableService"]["message"] is not None
    assert response.json()["data"]["enableService"]["success"] is True


API_DISABLE_SERVICE_MUTATION = """
mutation disableService($service_id: String!) {
    disableService(service_id: $service_id) {
        success
        message
        code
    }
}
"""


def test_graphql_disable_service_unathorized_client(
    client, mock_get_service_by_id_return_none, mock_nextcloud
):
    response = client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_disable_not_found_service(
    authorized_client, mock_get_service_by_id_return_none, mock_nextcloud
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["disableService"]["code"] == 404
    assert response.json()["data"]["disableService"]["message"] is not None
    assert response.json()["data"]["disableService"]["success"] is False


def test_graphql_disable_services(
    authorized_client, mock_get_service_by_id, mock_nextcloud
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_DISABLE_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["disableService"]["code"] == 200
    assert response.json()["data"]["disableService"]["message"] is not None
    assert response.json()["data"]["disableService"]["success"] is True


API_STOP_SERVICE_MUTATION = """
mutation stopService($service_id: String!) {
    stopService(service_id: $service_id) {
        success
        message
        code
    }
}
"""


def test_graphql_stop_service_unathorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_stop_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["stopService"]["code"] == 404
    assert response.json()["data"]["stopService"]["message"] is not None
    assert response.json()["data"]["stopService"]["success"] is False


def test_graphql_stop_services(
    authorized_client,
    mock_get_service_by_id,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_STOP_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["stopService"]["code"] == 200
    assert response.json()["data"]["stopService"]["message"] is not None
    assert response.json()["data"]["stopService"]["success"] is True


API_START_SERVICE_MUTATION = """
mutation startService($service_id: String!) {
    startService(service_id: $service_id) {
        success
        message
        code
    }
}
"""


def test_graphql_start_service_unathorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_start_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["startService"]["code"] == 404
    assert response.json()["data"]["startService"]["message"] is not None
    assert response.json()["data"]["startService"]["success"] is False


def test_graphql_start_services(
    authorized_client,
    mock_get_service_by_id,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_START_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["startService"]["code"] == 200
    assert response.json()["data"]["startService"]["message"] is not None
    assert response.json()["data"]["startService"]["success"] is True


API_RESTART_SERVICE_MUTATION = """
mutation restartService($service_id: String!) {
    restartService(service_id: $service_id) {
        success
        message
        code
    }
}
"""


def test_graphql_restart_service_unathorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_restart_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
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
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESTART_SERVICE_MUTATION,
            "variables": {"service_id": "nextcloud"},
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


def test_graphql_move_service_unathorized_client(
    client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"service_id": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_move_not_found_service(
    authorized_client,
    mock_get_service_by_id_return_none,
    mock_nextcloud,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"service_id": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 404
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_not_moveble_service(
    authorized_client,
    mock_get_service_by_id,
    mock_nextcloud_return_false,
    mock_service_to_graphql_service,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"service_id": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 400
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_service_volume_not_found(
    authorized_client,
    mock_get_service_by_id,
    mock_nextcloud,
    mock_service_to_graphql_service,
    mock_block_devices_return_none,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"service_id": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 400
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is False


def test_graphql_move_service(
    authorized_client,
    mock_get_service_by_id,
    mock_nextcloud,
    mock_service_to_graphql_service,
    mock_block_devices,
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOVE_SERVICE_MUTATION,
            "variables": {
                "input": {"service_id": "nextcloud", "location": "sdx"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["moveService"]["code"] == 200
    assert response.json()["data"]["moveService"]["message"] is not None
    assert response.json()["data"]["moveService"]["success"] is True
