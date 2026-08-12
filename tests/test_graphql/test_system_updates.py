from unittest.mock import AsyncMock

from selfprivacy_api.exceptions.system import UnknownUpdateChannel
from selfprivacy_api.update_channels import UPDATE_CHANNELS

from tests.common import generate_system_query
from tests.test_graphql.common import (
    assert_empty,
    assert_errorcode,
    assert_ok,
    get_data,
)


API_SYSTEM_UPDATES_QUERY = """
updates {
    currentChannel {
        id
        updateUrl
        name
        description
    }
    channels {
        id
        updateUrl
        name
        description
    }
}
"""

API_SET_UPDATE_CHANNEL_MUTATION = """
mutation setUpdateChannel($channelId: String!) {
    system {
        setUpdateChannel(channelId: $channelId) {
            success
            message
            code
        }
    }
}
"""

STABLE_CHANNEL = UPDATE_CHANNELS[0]


class FlakeManagerStub:
    def __init__(self, nixos_config):
        self.nixos_config = nixos_config

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def test_get_system_updates_known_channel(authorized_client, mocker):
    manager_factory = mocker.patch(
        "selfprivacy_api.graphql.queries.system.FlakeServiceManager",
        return_value=FlakeManagerStub(STABLE_CHANNEL.update_url),
    )

    response = authorized_client.post(
        "/graphql",
        json={"query": generate_system_query([API_SYSTEM_UPDATES_QUERY])},
    )

    updates = get_data(response)["system"]["updates"]
    current_channel = updates["currentChannel"]
    assert current_channel["id"] == STABLE_CHANNEL.id
    assert current_channel["updateUrl"] == STABLE_CHANNEL.update_url
    assert updates["channels"]
    assert set(updates["channels"][0]) == {
        "id",
        "updateUrl",
        "name",
        "description",
    }
    manager_factory.assert_called_once_with()


def test_get_system_updates_custom_channel(authorized_client, mocker):
    current_url = "git+https://example.org/config?ref=testing"
    mocker.patch(
        "selfprivacy_api.graphql.queries.system.FlakeServiceManager",
        return_value=FlakeManagerStub(current_url),
    )

    response = authorized_client.post(
        "/graphql",
        json={"query": generate_system_query([API_SYSTEM_UPDATES_QUERY])},
    )

    current_channel = get_data(response)["system"]["updates"]["currentChannel"]
    assert current_channel["id"] == "custom"
    assert current_channel["updateUrl"] == current_url


def test_get_system_updates_unauthorized(client, mocker):
    manager_factory = mocker.patch(
        "selfprivacy_api.graphql.queries.system.FlakeServiceManager"
    )

    response = client.post(
        "/graphql",
        json={"query": generate_system_query([API_SYSTEM_UPDATES_QUERY])},
    )

    assert_empty(response)
    manager_factory.assert_not_called()


def test_set_update_channel(authorized_client, mocker):
    set_update_channel = mocker.patch(
        "selfprivacy_api.graphql.mutations.system_mutations.system_actions.set_system_update_channel",
        new_callable=AsyncMock,
    )

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_UPDATE_CHANNEL_MUTATION,
            "variables": {"channelId": STABLE_CHANNEL.id},
        },
    )

    data = get_data(response)["system"]["setUpdateChannel"]
    assert_ok(data)
    set_update_channel.assert_awaited_once_with(STABLE_CHANNEL.id)


def test_set_update_channel_unknown_channel(authorized_client, mocker):
    set_update_channel = mocker.patch(
        "selfprivacy_api.graphql.mutations.system_mutations.system_actions.set_system_update_channel",
        new_callable=AsyncMock,
        side_effect=UnknownUpdateChannel("no-such-channel", log=False),
    )

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_UPDATE_CHANNEL_MUTATION,
            "variables": {"channelId": "no-such-channel"},
        },
    )

    data = get_data(response)["system"]["setUpdateChannel"]
    assert_errorcode(data, 400)
    assert "no-such-channel" in data["message"]
    set_update_channel.assert_awaited_once_with("no-such-channel")


def test_set_update_channel_returns_action_error(authorized_client, mocker):
    set_update_channel = mocker.patch(
        "selfprivacy_api.graphql.mutations.system_mutations.system_actions.set_system_update_channel",
        new_callable=AsyncMock,
        side_effect=Exception("boom"),
    )

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_SET_UPDATE_CHANNEL_MUTATION,
            "variables": {"channelId": STABLE_CHANNEL.id},
        },
    )

    data = get_data(response)["system"]["setUpdateChannel"]
    assert_errorcode(data, 400)
    assert "boom" in data["message"]
    set_update_channel.assert_awaited_once_with(STABLE_CHANNEL.id)


def test_set_update_channel_unauthorized(client, mocker):
    set_update_channel = mocker.patch(
        "selfprivacy_api.graphql.mutations.system_mutations.system_actions.set_system_update_channel",
        new_callable=AsyncMock,
    )

    response = client.post(
        "/graphql",
        json={
            "query": API_SET_UPDATE_CHANNEL_MUTATION,
            "variables": {"channelId": STABLE_CHANNEL.id},
        },
    )

    assert_empty(response)
    set_update_channel.assert_not_awaited()
