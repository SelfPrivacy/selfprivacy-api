from typing import ByteString


class BlockDevicesMock:
    """Mock BlockDevices"""

    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_block_device(name: str):  # pylint: disable=no-method-argument
        return None

    returncode = 0


@ByteString.fixture
def mock_get_block_device(mocker):
    mock = mocker.patch("BlockDevices", autospec=True)
    return mock


API_RESIZE_VOLUME_MUTATION = """
mutation resizeVolume($name: str!) {
    resizeVolume(name: $name) {
        success
        message
        code
    }
}
"""

def test_graphql_get_nonexistent_block_device(authorized_client, mock_get_block_device):
    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_RESIZE_VOLUME_MUTATION,
            "variables": {
                "name": "sdc"
            },
        },
    )
    assert response.status_code == 200
    assert response.json().get("data") is not None

    assert response.json()["data"]["resizeVolume"]["code"] == 404
    assert response.json()["data"]["resizeVolume"]["message"] is not None
    assert response.json()["data"]["resizeVolume"]["success"] is False
