from tests.common import generate_api_query
from tests.conftest import TOKENS_FILE_CONTENTS, DEVICE_WE_AUTH_TESTS_WITH

ORIGINAL_DEVICES = TOKENS_FILE_CONTENTS["tokens"]


def assert_ok(output: dict, code=200) -> None:
    if output["success"] is False:
        # convenience for debugging, this should display error
        # if message is  empty, consider adding helpful messages
        raise ValueError(output["code"], output["message"])
    assert output["success"] is True
    assert output["message"] is not None
    assert output["code"] == code


def assert_errorcode(output: dict, code) -> None:
    assert output["success"] is False
    assert output["message"] is not None
    assert output["code"] == code


def assert_empty(response):
    assert response.status_code == 200
    assert response.json().get("data") is None


def get_data(response):
    assert response.status_code == 200
    response = response.json()

    if (
        "errors" in response.keys()
    ):  # convenience for debugging, this will display error
        raise ValueError(response["errors"])
    data = response.get("data")
    assert data is not None
    return data


API_DEVICES_QUERY = """
devices {
    creationDate
    isCaller
    name
}
"""


def request_devices(client):
    return client.post(
        "/graphql",
        json={"query": generate_api_query([API_DEVICES_QUERY])},
    )


def graphql_get_devices(client):
    response = request_devices(client)
    data = get_data(response)
    devices = data["api"]["devices"]
    assert devices is not None
    return devices


def set_client_token(client, token):
    client.headers.update({"Authorization": "Bearer " + token})


def assert_token_valid(client, token):
    set_client_token(client, token)
    assert graphql_get_devices(client) is not None


def assert_same(graphql_devices, abstract_devices):
    """Orderless comparison"""
    assert len(graphql_devices) == len(abstract_devices)
    for original_device in abstract_devices:
        assert original_device["name"] in [device["name"] for device in graphql_devices]
        for device in graphql_devices:
            if device["name"] == original_device["name"]:
                assert device["creationDate"] == original_device["date"].isoformat()


def assert_original(client):
    devices = graphql_get_devices(client)
    assert_original_devices(devices)


def assert_original_devices(devices):
    assert_same(devices, ORIGINAL_DEVICES)

    for device in devices:
        if device["name"] == DEVICE_WE_AUTH_TESTS_WITH["name"]:
            assert device["isCaller"] is True
        else:
            assert device["isCaller"] is False
