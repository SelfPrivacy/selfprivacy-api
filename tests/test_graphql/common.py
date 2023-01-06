from tests.common import generate_api_query
from tests.conftest import TOKENS_FILE_CONTENTS, DEVICE_WE_AUTH_TESTS_WITH

ORIGINAL_DEVICES = TOKENS_FILE_CONTENTS["tokens"]


def assert_ok(response, request):
    data = assert_data(response)
    data[request]["success"] is True
    data[request]["message"] is not None
    data[request]["code"] == 200


def assert_errorcode(response, request, code):
    data = assert_data(response)
    data[request]["success"] is False
    data[request]["message"] is not None
    data[request]["code"] == code


def assert_empty(response):
    assert response.status_code == 200
    assert response.json().get("data") is None


def assert_data(response):
    assert response.status_code == 200
    data = response.json().get("data")
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
    data = assert_data(response)
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
    assert_same(devices, ORIGINAL_DEVICES)

    for device in devices:
        if device["name"] == DEVICE_WE_AUTH_TESTS_WITH["name"]:
            assert device["isCaller"] is True
        else:
            assert device["isCaller"] is False
