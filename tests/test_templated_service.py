import copy
import json
from typing import Any

import pytest

from selfprivacy_api.models.services import ServiceStatus, SupportLevel
from selfprivacy_api.services.config_item import (
    BoolServiceConfigItem,
    EnumServiceConfigItem,
    IntServiceConfigItem,
    StringServiceConfigItem,
)
from selfprivacy_api.services.templated_service import (
    TemplatedService,
    config_item_from_json,
)

JSONDict = dict[str, Any]

SERVICE_SYSTEMD_UNITS: list[str] = [
    "matrix-synapse.service",
    "matrix-authentication-service.service",
    "mas-kanidm-sync.service",
]

SERVICE_META: JSONDict = {
    "id": "matrix",
    "name": "Matrix",
    "description": "An open network for secure, decentralised communication",
    "svgIcon": "<svg></svg>",
    "isMovable": True,
    "backupDescription": "Messages, sessions, server signing keys and attachments",
    "systemdServices": SERVICE_SYSTEMD_UNITS,
    "license": [
        {
            "deprecated": False,
            "free": True,
            "fullName": "GNU Affero General Public License v3.0 or later",
            "redistributable": True,
            "shortName": "agpl3Plus",
            "spdxId": "AGPL-3.0-or-later",
            "url": "https://spdx.org/licenses/AGPL-3.0-or-later.html",
        },
    ],
    "homepage": "https://matrix.org",
    "sourcePage": "https://github.com/element-hq",
    "supportLevel": "experimental",
}

SERVICE_SUBDOMAIN_META: JSONDict = {
    "widget": "subdomain",
    "type": "string",
    "regex": "[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]",
}

SERVICE_OPTIONS: JSONDict = {
    "enable": {
        "name": "enable",
        "default": False,
        "description": "Enable Matrix",
        "meta": {"type": "enable"},
    },
    "location": {
        "name": "location",
        "default": None,
        "description": "Data location",
        "meta": {"type": "location"},
    },
    "subdomain": {
        "name": "subdomain",
        "default": "synapse",
        "description": "Matrix server subdomain",
        "meta": SERVICE_SUBDOMAIN_META | {"weight": 0},
    },
    "elementSubdomain": {
        "name": "elementSubdomain",
        "default": "element",
        "description": "Element client subdomain",
        "meta": SERVICE_SUBDOMAIN_META | {"weight": 1},
    },
    "masSubdomain": {
        "name": "masSubdomain",
        "default": "mas",
        "description": "Matrix Authentication Service subdomain",
        "meta": SERVICE_SUBDOMAIN_META | {"weight": 2},
    },
    "allowToPublishRoomsIntoDirectory": {
        "name": "allowToPublishRoomsIntoDirectory",
        "default": False,
        "description": "Allow all users to publish rooms into server room directory",
        "meta": {"type": "bool", "weight": 3},
    },
}


def service_definition_data() -> JSONDict:
    return {
        "meta": copy.deepcopy(SERVICE_META),
        "options": copy.deepcopy(SERVICE_OPTIONS),
    }


def service_definition(definition: JSONDict | None = None) -> str:
    if definition is None:
        definition = service_definition_data()
    return json.dumps(definition)


def test_templated_service_requires_meta():
    definition = service_definition_data()
    definition.pop("meta")

    with pytest.raises(ValueError, match="meta not found"):
        TemplatedService("matrix", service_definition(definition))


def test_templated_service_requires_options():
    definition = service_definition_data()
    definition.pop("options")

    with pytest.raises(ValueError, match="options not found"):
        TemplatedService("matrix", service_definition(definition))


def test_movable_templated_service_requires_location_option():
    definition = service_definition_data()
    definition["options"].pop("location")

    with pytest.raises(ValueError, match="does not have a location option"):
        TemplatedService(
            "matrix",
            service_definition(definition),
        )


@pytest.mark.parametrize("service_id", ["../matrix", r"matrix\child"])
def test_templated_service_rejects_path_like_ids(service_id):
    definition = service_definition_data()
    definition["meta"]["id"] = service_id

    service = TemplatedService(
        "matrix",
        service_definition(definition),
    )

    with pytest.raises(ValueError, match="Invalid ID"):
        service.get_id()


@pytest.mark.parametrize(
    "json_data",
    [
        {"name": "enable", "default": False, "description": "Enable Matrix"},
        {
            "name": "missing_type",
            "default": False,
            "description": "Missing type",
            "meta": {},
        },
        {
            "name": "enable",
            "default": False,
            "description": "Enable Matrix",
            "meta": {"type": "enable"},
        },
        {
            "name": "location",
            "default": None,
            "description": "Data location",
            "meta": {"type": "location"},
        },
    ],
)
def test_config_item_from_json_returns_none_for_non_config_options(json_data):
    assert config_item_from_json(json_data) is None


@pytest.mark.parametrize(
    ("json_data", "expected_type", "expected_widget", "expected_weight"),
    [
        (
            {
                "name": "elementSubdomain",
                "default": "element",
                "description": "Element client subdomain",
                "meta": {
                    "type": "string",
                    "widget": "subdomain",
                    "regex": "[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]",
                    "weight": 1,
                },
            },
            StringServiceConfigItem,
            "subdomain",
            1,
        ),
        (
            {
                "name": "allowToPublishRoomsIntoDirectory",
                "default": False,
                "description": (
                    "Allow all users to publish rooms into server room directory"
                ),
                "meta": {"type": "bool", "weight": 3},
            },
            BoolServiceConfigItem,
            "switch",
            3,
        ),
        (
            {
                "name": "mode",
                "default": "small",
                "description": "Mode",
                "meta": {"type": "enum", "options": ["small", "large"]},
            },
            EnumServiceConfigItem,
            "select",
            50,
        ),
        (
            {
                "name": "workers",
                "default": 2,
                "description": "Workers",
                "meta": {"type": "int", "minValue": 1, "maxValue": 8},
            },
            IntServiceConfigItem,
            "number",
            50,
        ),
    ],
)
def test_config_item_from_json_builds_config_items(
    json_data, expected_type, expected_widget, expected_weight
):
    config_item = config_item_from_json(json_data)

    assert isinstance(config_item, expected_type)
    assert config_item.id == json_data["name"]
    assert config_item.description == json_data["description"]
    assert config_item.widget == expected_widget
    assert config_item.weight == expected_weight


def test_config_item_from_json_uses_custom_weight():
    config_item = config_item_from_json(
        {
            "name": "masSubdomain",
            "default": "mas",
            "description": "Matrix Authentication Service subdomain",
            "meta": {
                "type": "string",
                "widget": "subdomain",
                "regex": "[A-Za-z0-9][A-Za-z0-9-]{0,61}[A-Za-z0-9]",
                "weight": 2,
            },
        }
    )

    assert config_item.weight == 2


def test_config_item_from_json_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown config item type"):
        config_item_from_json(
            {
                "name": "unknown",
                "default": "value",
                "description": "Unknown",
                "meta": {"type": "unknown"},
            }
        )


def test_templated_service_metadata_accessors():
    definition = service_definition_data()
    definition["meta"]["sso"] = {
        "userGroup": "sp.matrix.users",
        "adminGroup": "sp.matrix.admins",
    }

    service = TemplatedService("matrix", service_definition(definition))

    assert service.get_id() == "matrix"
    assert service.get_display_name() == "Matrix"
    assert (
        service.get_description()
        == "An open network for secure, decentralised communication"
    )
    assert service.get_svg_icon(raw=True) == "<svg></svg>"
    assert service.get_svg_icon() == "PHN2Zz48L3N2Zz4="
    assert service.get_user() == "matrix"
    assert service.get_group() == "matrix"
    assert service.is_movable() is True
    assert service.is_required() is False
    assert service.can_be_backed_up() is True
    assert (
        service.get_backup_description()
        == "Messages, sessions, server signing keys and attachments"
    )
    assert service.get_homepage() == "https://matrix.org"
    assert service.get_source_page() == "https://github.com/element-hq"
    assert service.get_support_level() is SupportLevel.EXPERIMENTAL
    assert service.get_sso_user_group() == "sp.matrix.users"
    assert service.get_sso_admin_group() == "sp.matrix.admins"
    assert service.get_license()[0].spdx_id == "AGPL-3.0-or-later"


def test_templated_service_user_and_group_defaults_to_service_id():
    service = TemplatedService("matrix", service_definition())

    assert service.get_user() == "matrix"
    assert service.get_group() == "matrix"


def test_templated_service_sso_accessors_return_none_without_sso_config():
    service = TemplatedService("matrix", service_definition())

    assert service.get_sso_user_group() is None
    assert service.get_sso_admin_group() is None


def test_templated_service_get_url_returns_none_when_hidden():
    definition = service_definition_data()
    definition["meta"]["showUrl"] = False

    service = TemplatedService(
        "matrix",
        service_definition(definition),
    )

    assert service.get_url() is None


@pytest.mark.asyncio
async def test_templated_service_get_status_uses_service_systemd_units(mocker):
    get_status = mocker.patch(
        "selfprivacy_api.services.templated_service."
        "get_service_status_from_several_units",
        return_value=ServiceStatus.INACTIVE,
    )
    service = TemplatedService("matrix", service_definition())

    assert await service.get_status() is ServiceStatus.INACTIVE
    get_status.assert_awaited_once_with(SERVICE_SYSTEMD_UNITS)
