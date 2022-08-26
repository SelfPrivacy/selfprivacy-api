import pytest


class BlockDevicesMockReturnNone:
    """Mock BlockDevices"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_block_device(self, name: str):
        return None

    def resize(self):
        pass

    returncode = 0


class BlockDevicesMock:
    """Mock BlockDevices"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_block_device(self, name: str):
        return 0

    def resize(self):
        pass

    returncode = 0


@pytest.fixture
def mock_block_device_return_none(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.storage_mutation.BlockDevices", autospec=True
    )
    return mock


@pytest.fixture
def mock_block_device_return(mocker):
    mock = mocker.patch(
        "selfprivacy_api.graphql.mutations.storage_mutation.BlockDevices", autospec=True
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


def test_graphql_resize_volumea_unathorized_client(client, mock_block_device):
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
    authorized_client, mock_block_device
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


def test_graphql_resize_volume(authorized_client, mock_block_device):
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
