"""
Tests for get_templated_service() and get_templated_services() from
selfprivacy_api.services.
"""

import json
import logging
from os import makedirs

import pytest

from selfprivacy_api.services import get_templated_service, get_templated_services
from selfprivacy_api.services.templated_service import TemplatedService
from tests.conftest import (
    install_module_definition,
    install_real_module_definition,
    read_module_definition,
)

# --- get_templated_service -----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_templated_service_loads_real_definition(sp_modules_dir):
    definition = read_module_definition("gitea")
    install_module_definition(sp_modules_dir, "gitea", definition)

    service = await get_templated_service("gitea")

    assert isinstance(service, TemplatedService)
    assert service.get_id() == "gitea"
    assert service.get_display_name() == "Forgejo"
    assert service.is_movable() is True
    assert service.definition_data == json.loads(definition)

    licenses = service.get_license()
    assert len(licenses) == 1
    assert licenses[0].spdx_id == "GPL-3.0-or-later"
    assert licenses[0].full_name == "GNU General Public License v3.0 or later"
    assert licenses[0].free is True


@pytest.mark.asyncio
async def test_get_templated_service_missing_definition_raises(sp_modules_dir):
    install_real_module_definition(sp_modules_dir, "gitea")

    with pytest.raises(FileNotFoundError, match="nextcloud"):
        await get_templated_service("nextcloud")


@pytest.mark.asyncio
async def test_get_templated_service_missing_directory_raises(sp_modules_dir):
    # sp_modules_dir does not create the directory itself.
    with pytest.raises(FileNotFoundError, match="gitea"):
        await get_templated_service("gitea")


@pytest.mark.asyncio
async def test_get_templated_service_malformed_json_raises(sp_modules_dir):
    install_module_definition(sp_modules_dir, "broken", "{not json")

    with pytest.raises(json.JSONDecodeError):
        await get_templated_service("broken")


@pytest.mark.asyncio
async def test_get_templated_service_incomplete_definition_raises(sp_modules_dir):
    install_module_definition(sp_modules_dir, "no-meta", json.dumps({"options": {}}))
    install_module_definition(
        sp_modules_dir, "no-options", json.dumps({"meta": {"id": "no-options"}})
    )

    with pytest.raises(ValueError, match="meta"):
        await get_templated_service("no-meta")
    with pytest.raises(ValueError, match="options"):
        await get_templated_service("no-options")


@pytest.mark.asyncio
async def test_get_templated_service_served_from_cache_when_unchanged(sp_modules_dir):
    install_real_module_definition(sp_modules_dir, "gitea")

    first = await get_templated_service("gitea")
    second = await get_templated_service("gitea")

    assert second is first


@pytest.mark.asyncio
async def test_get_templated_service_cache_invalidated_when_file_changes(
    sp_modules_dir,
):
    install_module_definition(sp_modules_dir, "svc", read_module_definition("gitea"))
    first = await get_templated_service("svc")
    assert first.get_id() == "gitea"

    install_module_definition(
        sp_modules_dir, "svc", read_module_definition("nextcloud")
    )
    second = await get_templated_service("svc")

    assert second is not first
    assert second.get_id() == "nextcloud"


# --- get_templated_services ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_templated_services_no_directory_returns_empty(sp_modules_dir):
    assert await get_templated_services(ignored_services=[]) == []


@pytest.mark.asyncio
async def test_get_templated_services_empty_directory_returns_empty(sp_modules_dir):
    makedirs(sp_modules_dir)
    assert await get_templated_services(ignored_services=[]) == []


@pytest.mark.asyncio
async def test_get_templated_services_loads_all_installed(sp_modules_dir):
    install_real_module_definition(sp_modules_dir, "gitea")
    install_real_module_definition(sp_modules_dir, "nextcloud")

    services = await get_templated_services(ignored_services=[])

    assert all(isinstance(service, TemplatedService) for service in services)
    assert {service.get_id() for service in services} == {"gitea", "nextcloud"}


@pytest.mark.asyncio
async def test_get_templated_services_skips_ignored(sp_modules_dir):
    install_real_module_definition(sp_modules_dir, "gitea")
    install_real_module_definition(sp_modules_dir, "nextcloud")

    services = await get_templated_services(ignored_services=["gitea"])
    assert [service.get_id() for service in services] == ["nextcloud"]

    assert await get_templated_services(ignored_services=["gitea", "nextcloud"]) == []


@pytest.mark.asyncio
async def test_get_templated_services_broken_definition_skipped_and_logged(
    sp_modules_dir, caplog
):
    install_real_module_definition(sp_modules_dir, "gitea")
    install_module_definition(sp_modules_dir, "broken", "{not json")

    with caplog.at_level(logging.ERROR, logger="selfprivacy_api.services"):
        services = await get_templated_services(ignored_services=[])

    assert [service.get_id() for service in services] == ["gitea"]
    assert "Failed to load service" in caplog.text
