"""
Tests for selfprivacy_api.services.suggested.SuggestedServices.
"""

import json
from os.path import join
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio

from selfprivacy_api.services.suggested import SuggestedServices
from selfprivacy_api.services.templated_service import TemplatedService
from selfprivacy_api.utils.redis_pool import RedisPool
from tests.conftest import (
    HttpxApiRecorder,
    global_data_dir,
    install_module_definition,
    read_module_definition,
)

FORGEJO_CONTENTS_URL = (
    "https://git.selfprivacy.org/api/v1/repos/SelfPrivacy"
    "/selfprivacy-nixos-config/contents/sp-modules"
)

FORGEJO_ERROR_RESPONSE = {
    "errors": None,
    "message": "GetContentsOrList",
    "url": "https://git.selfprivacy.org/api/swagger",
}


def read_forgejo_response() -> list:
    with open(
        join(global_data_dir(), "forgejo_sp_modules_response.json"), encoding="utf-8"
    ) as file:
        return json.load(file)


def module_flake_url(name: str, rev: str) -> str:
    return (
        "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git"
        f"?ref=flakes&rev={rev}&dir=sp-modules/{name}"
    )


@pytest_asyncio.fixture
async def suggested_redis():
    redis = RedisPool().get_connection_async()

    async def clear():
        async for key in redis.scan_iter("suggestedservices:*"):
            await redis.delete(key)

    await clear()
    yield redis
    await clear()
    await redis.aclose()


@pytest.fixture
def forgejo_api(mocker):
    """Reroute httpx.AsyncClient as looked up by the suggested services module."""
    recorder = HttpxApiRecorder()
    transport = httpx.MockTransport(recorder)
    real_async_client = httpx.AsyncClient

    def client_factory(**kwargs):
        return real_async_client(transport=transport, **kwargs)

    mocker.patch(
        "selfprivacy_api.services.suggested.httpx.AsyncClient", new=client_factory
    )
    return recorder


@pytest.fixture
def remote_service_mock(mocker):
    """
    Replace get_remote_service (normally calls sp-fetch-remote-module)
    with a mock returning the real definition for the requested module.
    """

    async def fake_remote_service(name: str, url: str) -> TemplatedService:
        return TemplatedService(name, read_module_definition(name))

    mock = AsyncMock(side_effect=fake_remote_service)
    mocker.patch("selfprivacy_api.services.suggested.get_remote_service", new=mock)
    return mock


# --- SuggestedServices.sync() --------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_fresh_cache_fetches_all_modules(
    suggested_redis, forgejo_api, remote_service_mock
):
    modules = read_forgejo_response()
    forgejo_api.respond(200, modules)

    await SuggestedServices.sync()

    assert len(forgejo_api.requests) == 1
    request = forgejo_api.requests[0]
    assert str(request.url) == FORGEJO_CONTENTS_URL
    assert request.headers["Accept"] == "application/json"

    fetched_urls = {
        call.args[0]: call.args[1] for call in remote_service_mock.call_args_list
    }
    assert len(fetched_urls) == len(modules)
    for module in modules:
        name = module["name"]
        rev = module["last_commit_sha"]
        assert fetched_urls[name] == module_flake_url(name, rev)
        assert await suggested_redis.get(f"suggestedservices:{name}:HEAD") == rev
        cached_data = await suggested_redis.get(f"suggestedservices:{name}:data")
        assert json.loads(cached_data) == json.loads(read_module_definition(name))


@pytest.mark.asyncio
async def test_sync_skips_up_to_date_modules(
    suggested_redis, forgejo_api, remote_service_mock
):
    modules = read_forgejo_response()
    for module in modules:
        await suggested_redis.set(
            f"suggestedservices:{module['name']}:HEAD", module["last_commit_sha"]
        )
    forgejo_api.respond(200, modules)

    await SuggestedServices.sync()

    remote_service_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_refetches_only_stale_modules(
    suggested_redis, forgejo_api, remote_service_mock
):
    modules = read_forgejo_response()
    stale, fresh = modules[0], modules[1]
    await suggested_redis.set(
        f"suggestedservices:{stale['name']}:HEAD",
        "0000000000000000000000000000000000000000",
    )
    await suggested_redis.set(
        f"suggestedservices:{fresh['name']}:HEAD", fresh["last_commit_sha"]
    )
    forgejo_api.respond(200, modules)

    await SuggestedServices.sync()

    remote_service_mock.assert_awaited_once()
    assert remote_service_mock.call_args.args[0] == stale["name"]
    assert (
        await suggested_redis.get(f"suggestedservices:{stale['name']}:HEAD")
        == stale["last_commit_sha"]
    )


@pytest.mark.asyncio
async def test_sync_non_list_response_raises(
    suggested_redis, forgejo_api, remote_service_mock
):
    forgejo_api.respond(404, FORGEJO_ERROR_RESPONSE)

    with pytest.raises(AssertionError):
        await SuggestedServices.sync()

    remote_service_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_propagates_fetch_failures_and_caches_nothing(
    suggested_redis, forgejo_api, remote_service_mock
):
    modules = read_forgejo_response()
    forgejo_api.respond(200, modules)
    remote_service_mock.side_effect = Exception("fetch failed")

    with pytest.raises(ExceptionGroup):
        await SuggestedServices.sync()

    for module in modules:
        name = module["name"]
        assert await suggested_redis.get(f"suggestedservices:{name}:data") is None


# --- SuggestedServices.get() ---------------------------------------------------------


async def seed_cached_module(redis, name: str) -> dict:
    definition = json.loads(read_module_definition(name))
    await redis.set(f"suggestedservices:{name}:data", json.dumps(definition))
    await redis.set(
        f"suggestedservices:{name}:HEAD", "f4b5ef270d75c23f2fddcd3def5e8e14c323ee65"
    )
    return definition


@pytest.mark.asyncio
async def test_get_empty_cache_returns_nothing(suggested_redis):
    assert await SuggestedServices.get() == []


@pytest.mark.asyncio
async def test_get_returns_cached_services(suggested_redis, sp_modules_dir):
    definitions = {}
    for name in ("gitea", "nextcloud"):
        definitions[name] = await seed_cached_module(suggested_redis, name)

    services = await SuggestedServices.get()

    # :HEAD keys must not have produced extra entries.
    assert len(services) == 2
    assert all(isinstance(service, TemplatedService) for service in services)
    by_id = {service.get_id(): service for service in services}
    assert set(by_id.keys()) == {"gitea", "nextcloud"}
    for name, definition in definitions.items():
        assert by_id[name].definition_data == definition


@pytest.mark.asyncio
async def test_get_skips_installed_services(suggested_redis, sp_modules_dir):
    install_module_definition(sp_modules_dir, "gitea", read_module_definition("gitea"))
    for name in ("gitea", "nextcloud"):
        await seed_cached_module(suggested_redis, name)

    services = await SuggestedServices.get()

    assert [service.get_id() for service in services] == ["nextcloud"]
