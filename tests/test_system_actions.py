from unittest.mock import AsyncMock

import pytest

from selfprivacy_api.actions.system import (
    set_system_update_channel,
    set_system_update_url,
)
from selfprivacy_api.exceptions.system import UnknownUpdateChannel
from selfprivacy_api.update_channels import UPDATE_CHANNELS


class FlakeManagerStub:
    def __init__(self, services, nixos_config):
        self.services = services
        self.nixos_config = nixos_config

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


async def test_set_system_update_url_updates_matching_service_modules(mocker):
    old_url = (
        "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git"
        "?ref=flakes"
    )
    new_url = (
        "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git"
        "?ref=testing"
    )
    services = {
        "nextcloud": f"{old_url}&dir=sp-modules/nextcloud",
        "external": "git+https://example.org/service?ref=flakes&dir=sp-modules/external",
        "not-a-module": f"{old_url}&dir=other",
    }
    manager = FlakeManagerStub(services=services, nixos_config=old_url)
    manager_factory = mocker.patch(
        "selfprivacy_api.actions.system.FlakeServiceManager",
        return_value=manager,
    )

    await set_system_update_url(new_url)

    manager_factory.assert_called_once_with()
    assert manager.nixos_config == new_url
    assert manager.services == {
        "nextcloud": f"{new_url}&dir=sp-modules/nextcloud",
        "external": services["external"],
        "not-a-module": services["not-a-module"],
    }


async def test_set_system_update_channel_applies_channel_url(mocker):
    set_url = mocker.patch(
        "selfprivacy_api.actions.system.set_system_update_url",
        new_callable=AsyncMock,
    )

    await set_system_update_channel(UPDATE_CHANNELS[0].id)

    set_url.assert_awaited_once_with(UPDATE_CHANNELS[0].update_url)


async def test_set_system_update_channel_rejects_unknown_channel(mocker):
    set_url = mocker.patch(
        "selfprivacy_api.actions.system.set_system_update_url",
        new_callable=AsyncMock,
    )

    with pytest.raises(UnknownUpdateChannel):
        await set_system_update_channel("no-such-channel")

    set_url.assert_not_awaited()
