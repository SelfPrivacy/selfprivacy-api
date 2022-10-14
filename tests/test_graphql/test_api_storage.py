import pytest


class BlockDeviceMockReturnNone:
    """Mock BlockDevices"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def mount(self):
        return None

    def unmount(self):
        return None

    def resize(self):
        return None

    returncode = 0


class BlockDeviceMockReturnTrue:
    """Mock BlockDevices"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def mount(self):
        return True

    def unmount(self):
        return True

    def resize(self):
        return True

    returncode = 0


class BlockDeviceMockReturnFalse:
    """Mock BlockDevices"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def mount(self):
        return False

    def unmount(self):
        return False

    def resize(self):
        return False

    returncode = 0


class BlockDevicesMockReturnTrue:
    def get_block_device(name: str):  # type: ignore
        return BlockDeviceMockReturnTrue()

    def __new__(cls, *args, **kwargs):
        pass

    def __init__(self):
        pass


class BlockDevicesMockReturnNone:
    def get_block_device(name: str):  # type: ignore
        return None

    def __new__(cls, *args, **kwargs):
        pass

    def __init__(self):
        pass


@pytest.fixture
def mock_block_devices_return_true(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.storage_mutations.BlockDevices",
        # "selfprivacy_api.utils.block_devices.BlockDevices",
        autospec=True,
        return_value=BlockDevicesMockReturnTrue,
    )
    return mock


@pytest.fixture
def mock_block_devices_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevices",
        autospec=True,
        return_value=BlockDevicesMockReturnNone,
    )
    return mock


@pytest.fixture
def mock_block_device_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevice",
        autospec=True,
        return_value=BlockDeviceMockReturnNone,
    )
    return mock


@pytest.fixture
def mock_block_device_return_true(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevice",
        autospec=True,
        return_value=BlockDeviceMockReturnTrue,
    )
    return mock


@pytest.fixture
def mock_block_device_return_false(mocker):
    mock = mocker.patch(
        "selfprivacy_api.utils.block_devices.BlockDevice",
        autospec=True,
        return_value=BlockDeviceMockReturnFalse,
    )
    return mock


API_RESIZE_VOLUME_MUTATION = """
mutation resizeVolume($name: String!) {
    resizeVolume(name: $name) {
        success
        message
        code
    }
}
"""


def test_graphql_resize_volumea_unathorized_client(
    client, mock_block_devices_return_true
):
    response = client.post(
        "/graphql",
        json={
            "query": API_RESIZE_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_resize_volume_nonexistent_block_device(
    authorized_client, mock_block_devices_return_none
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESIZE_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["resizeVolume"]["code"] == 404
    assert response.json()["data"]["resizeVolume"]["message"] is not None
    assert response.json()["data"]["resizeVolume"]["success"] is False


def test_graphql_resize_volume(authorized_client, mock_block_devices_return_true):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESIZE_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["resizeVolume"]["code"] == 200
    assert response.json()["data"]["resizeVolume"]["message"] is not None
    assert response.json()["data"]["resizeVolume"]["success"] is True


API_MOUNT_VOLUME_MUTATION = """
mutation mountVolume($name: String!) {
    mountVolume(name: $name) {
        success
        message
        code
    }
}
"""


def test_graphql_mount_volume_unathorized_client(client, mock_block_device_return_true):
    response = client.post(
        "/graphql",
        json={
            "query": API_MOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_mount_already_mounted_volume(
    authorized_client, mock_block_devices_return_none
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["mountVolume"]["code"] == 404
    assert response.json()["data"]["mountVolume"]["message"] is not None
    assert response.json()["data"]["mountVolume"]["success"] is False


def test_graphql_mount_not_found_volume(
    authorized_client, mock_block_devices_return_none
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["mountVolume"]["code"] == 404
    assert response.json()["data"]["mountVolume"]["message"] is not None
    assert response.json()["data"]["mountVolume"]["success"] is False


def test_graphql_mount_volume(authorized_client, mock_block_devices_return_true):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_MOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["mountVolume"]["code"] == 200
    assert response.json()["data"]["mountVolume"]["message"] is not None
    assert response.json()["data"]["mountVolume"]["success"] is True


API_UNMOUNT_VOLUME_MUTATION = """
mutation unmountVolume($name: String!) {
    unmountVolume(name: $name) {
        success
        message
        code
    }
}
"""


def test_graphql_unmount_volume_unathorized_client(
    client, mock_block_devices_return_true
):
    response = client.post(
        "/graphql",
        json={
            "query": API_UNMOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is None


def test_graphql_unmount_not_fount_volume(
    authorized_client, mock_block_devices_return_true
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UNMOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["unmountVolume"]["code"] == 404
    assert response.json()["data"]["unmountVolume"]["message"] is not None
    assert response.json()["data"]["unmountVolume"]["success"] is False


def test_graphql_unmount_volume_false(
    authorized_client, mock_block_devices_return_true
):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UNMOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["unmountVolume"]["code"] == 404
    assert response.json()["data"]["unmountVolume"]["message"] is not None
    assert response.json()["data"]["unmountVolume"]["success"] is False


def test_graphql_unmount_volume(authorized_client, mock_block_devices_return_true):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_UNMOUNT_VOLUME_MUTATION,
            "variables": {"name": "sdx"},
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["unmountVolume"]["code"] == 200
    assert response.json()["data"]["unmountVolume"]["message"] is not None
    assert response.json()["data"]["unmountVolume"]["success"] is True
