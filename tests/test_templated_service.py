import json
from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from selfprivacy_api.models.services import (
    ServiceStatus,
    SupportLevel,
)
from selfprivacy_api.services.config_item import (
    BoolServiceConfigItem,
    EnumServiceConfigItem,
    IntServiceConfigItem,
    StringServiceConfigItem,
)
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.templated_service import (
    SP_SUGGESTED_MODULES_PATH,
    TemplatedService,
    config_item_from_json,
)
from selfprivacy_api.utils import WriteUserData

TEMPLATED_SERVICE_MODULE_PATH = "selfprivacy_api.services.templated_service"


# --- JSON fixture builder ------------------------------------------------------------


def _base_definition() -> dict:
    """Minimum viable service definition (non-movable, single systemd unit)."""
    return {
        "meta": {
            "id": "tsvc",
            "name": "Test Service",
            "description": "A test service",
            "svgIcon": "<svg/>",
            "showUrl": True,
            "isMovable": False,
            "isRequired": False,
            "canBeBackedUp": True,
            "backupDescription": "Backs up test data",
            "systemdServices": ["tsvc.service"],
            "user": "tsvc",
            "group": "tsvc",
            "folders": [],
            "ownedFolders": [],
            "postgreDatabases": [],
            "license": [],
            "homepage": "https://example.tld",
            "sourcePage": "https://example.tld/src",
            "supportLevel": "normal",
        },
        "options": {
            "enable": {
                "default": False,
                "description": "Enable",
                "name": "enable",
                "meta": {"type": "enable"},
            },
        },
    }


def _make_definition(**overrides) -> dict:
    definition = deepcopy(_base_definition())
    for key, value in overrides.items():
        if key == "meta_patch":
            definition["meta"].update(value)
        elif key == "options_patch":
            definition["options"].update(value)
        else:
            definition[key] = value
    return definition


def _make_service(**overrides) -> TemplatedService:
    return TemplatedService("tsvc", json.dumps(_make_definition(**overrides)))


def _add_location_option(options_patch: dict) -> dict:
    options_patch["location"] = {
        "default": None,
        "description": "Data location",
        "name": "location",
        "meta": {"type": "location"},
    }
    return options_patch


def _subdomain_option(name: str, default: str = "sub") -> dict:
    return {
        "default": default,
        "description": f"Subdomain {name}",
        "name": name,
        "meta": {
            "type": "string",
            "widget": "subdomain",
            "regex": "^[a-z0-9-]+$",
        },
    }


# --- config_item_from_json -----------------------------------------------------------


def test_config_item_from_json_returns_none_when_meta_absent():
    assert config_item_from_json({"name": "x", "default": None}) is None


def test_config_item_from_json_returns_none_when_type_absent():
    assert config_item_from_json({"name": "x", "meta": {}}) is None


def test_config_item_from_json_skips_enable_and_location():
    enable = {"name": "e", "default": False, "meta": {"type": "enable"}}
    location = {"name": "l", "default": None, "meta": {"type": "location"}}
    assert config_item_from_json(enable) is None
    assert config_item_from_json(location) is None


def test_config_item_from_json_string_full_meta():
    item = config_item_from_json(
        {
            "name": "sub",
            "default": "example",
            "description": "Subdomain",
            "meta": {
                "type": "string",
                "regex": "^[a-z]+$",
                "widget": "subdomain",
                "allowEmpty": False,
                "weight": 7,
            },
        }
    )
    assert isinstance(item, StringServiceConfigItem)
    assert item.id == "sub"
    assert item.default_value == "example"
    assert item.description == "Subdomain"
    assert item.regex is not None and item.regex.pattern == "^[a-z]+$"
    assert item.widget == "subdomain"
    assert item.allow_empty is False
    assert item.weight == 7


def test_config_item_from_json_string_minimal_defaults():
    item = config_item_from_json(
        {
            "name": "note",
            "default": "hi",
            "description": "d",
            "meta": {"type": "string"},
        }
    )
    assert isinstance(item, StringServiceConfigItem)
    assert item.regex is None
    assert item.widget == "text"
    assert item.allow_empty is False
    assert item.weight == 50


def test_config_item_from_json_bool():
    item = config_item_from_json(
        {
            "name": "flag",
            "default": True,
            "description": "d",
            "meta": {"type": "bool", "weight": 3},
        }
    )
    assert isinstance(item, BoolServiceConfigItem)
    assert item.default_value is True
    assert item.widget == "switch"
    assert item.weight == 3


def test_config_item_from_json_enum():
    item = config_item_from_json(
        {
            "name": "level",
            "default": "low",
            "description": "d",
            "meta": {
                "type": "enum",
                "options": ["low", "high"],
                "widget": "select",
            },
        }
    )
    assert isinstance(item, EnumServiceConfigItem)
    assert item.options == ["low", "high"]
    assert item.widget == "select"


def test_config_item_from_json_int():
    item = config_item_from_json(
        {
            "name": "n",
            "default": 5,
            "description": "d",
            "meta": {
                "type": "int",
                "widget": "number",
                "minValue": 1,
                "maxValue": 10,
            },
        }
    )
    assert isinstance(item, IntServiceConfigItem)
    assert item.default_value == 5
    assert item.min_value == 1
    assert item.max_value == 10


def test_config_item_from_json_unknown_type_raises():
    with pytest.raises(ValueError):
        config_item_from_json(
            {"name": "x", "default": None, "description": "d", "meta": {"type": "??"}}
        )


# --- TemplatedService.__init__ validation --------------------------------------------


def test_init_happy_path_populates_state():
    service = _make_service(
        options_patch={
            "sub": _subdomain_option("sub", default="mail"),
            "flag": {
                "default": True,
                "description": "d",
                "name": "flag",
                "meta": {"type": "bool"},
            },
        }
    )
    assert service.meta.id == "tsvc"
    assert "flag" in service.config_items
    assert "sub" in service.config_items
    assert service.subdomain_options == ["sub"]


def test_init_missing_meta_raises():
    payload = _make_definition()
    payload.pop("meta")
    with pytest.raises(ValueError, match="meta"):
        TemplatedService("tsvc", json.dumps(payload))


def test_init_missing_options_raises():
    payload = _make_definition()
    payload.pop("options")
    with pytest.raises(ValueError, match="options"):
        TemplatedService("tsvc", json.dumps(payload))


def test_init_movable_without_location_option_raises():
    with pytest.raises(ValueError, match="location"):
        _make_service(meta_patch={"isMovable": True})


def test_init_movable_with_location_option_ok():
    service = _make_service(
        meta_patch={"isMovable": True},
        options_patch=_add_location_option({}),
    )
    assert service.is_movable() is True


def test_init_subdomain_options_preserves_declaration_order():
    service = _make_service(
        options_patch={
            "primary": _subdomain_option("primary", default="p"),
            "secondary": _subdomain_option("secondary", default="s"),
        }
    )
    assert service.subdomain_options == ["primary", "secondary"]


def test_init_malformed_json_raises():
    with pytest.raises(json.JSONDecodeError):
        TemplatedService("tsvc", "{not json")


# --- Simple metadata getters ---------------------------------------------------------


def test_metadata_getters_reflect_definition():
    service = _make_service()
    assert service.get_id() == "tsvc"
    assert service.get_display_name() == "Test Service"
    assert service.get_description() == "A test service"
    assert service.get_backup_description() == "Backs up test data"
    assert service.get_homepage() == "https://example.tld"
    assert service.get_source_page() == "https://example.tld/src"
    assert service.get_support_level() == SupportLevel.NORMAL
    assert service.is_movable() is False
    assert service.is_required() is False
    assert service.can_be_backed_up() is True
    assert service.get_license() == []


def test_get_svg_icon_raw_and_base64():
    service = _make_service(meta_patch={"svgIcon": "<svg>x</svg>"})
    assert service.get_svg_icon(raw=True) == "<svg>x</svg>"
    # PHN2Zz54PC9zdmc+ == base64("<svg>x</svg>")
    assert service.get_svg_icon() == "PHN2Zz54PC9zdmc+"


def test_get_id_rejects_path_separators():
    service = _make_service()
    service.meta.id = "bad/id"
    with pytest.raises(ValueError):
        service.get_id()
    service.meta.id = "bad\\id"
    with pytest.raises(ValueError):
        service.get_id()


def test_get_user_falls_back_to_id():
    service = _make_service(meta_patch={"user": None, "group": None})
    assert service.get_user() == "tsvc"
    assert service.get_group() == "tsvc"


def test_get_user_group_use_explicit_values():
    service = _make_service(meta_patch={"user": "u", "group": "g"})
    assert service.get_user() == "u"
    assert service.get_group() == "g"


def test_sso_getters_none_when_sso_absent():
    service = _make_service()
    assert service.get_sso_user_group() is None
    assert service.get_sso_admin_group() is None


def test_sso_getters_return_group_names():
    service = _make_service(
        meta_patch={"sso": {"userGroup": "users", "adminGroup": "admins"}}
    )
    assert service.get_sso_user_group() == "users"
    assert service.get_sso_admin_group() == "admins"


# --- Subdomains, URL -----------------------------------------------------------------


def test_get_subdomain_none_when_no_options():
    service = _make_service()
    assert service.get_subdomain() is None


def test_get_subdomain_uses_primary_when_configured(generic_userdata):
    service = _make_service(
        meta_patch={"primarySubdomain": "primary"},
        options_patch={
            "primary": _subdomain_option("primary", default="p"),
            "secondary": _subdomain_option("secondary", default="s"),
        },
    )
    assert service.get_subdomain() == "p"


def test_get_subdomain_falls_back_to_first_option(generic_userdata):
    service = _make_service(
        options_patch={
            "primary": _subdomain_option("primary", default="p"),
            "secondary": _subdomain_option("secondary", default="s"),
        }
    )
    # primary_subdomain unset → first declared subdomain option
    assert service.get_subdomain() == "p"


def test_get_subdomain_reads_userdata_override(generic_userdata):
    service = _make_service(
        options_patch={"sub": _subdomain_option("sub", default="def")}
    )
    with WriteUserData() as data:
        data.setdefault("modules", {}).setdefault("tsvc", {})["sub"] = "chosen"
    assert service.get_subdomain() == "chosen"


def test_get_subdomains_merges_userdata_and_defaults(generic_userdata):
    service = _make_service(
        options_patch={
            "a": _subdomain_option("a", default="da"),
            "b": _subdomain_option("b", default="db"),
        }
    )
    with WriteUserData() as data:
        data.setdefault("modules", {}).setdefault("tsvc", {})["a"] = "chosen-a"
    assert service.get_subdomains() == ["chosen-a", "db"]


def test_get_url_none_when_show_url_false(generic_userdata):
    service = _make_service(
        meta_patch={"showUrl": False},
        options_patch={"sub": _subdomain_option("sub", default="mail")},
    )
    assert service.get_url() is None


def test_get_url_none_when_no_subdomain(generic_userdata):
    service = _make_service()
    assert service.get_url() is None


def test_get_url_composes_https(generic_userdata, mocker):
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.get_domain", return_value="example.tld"
    )
    service = _make_service(
        options_patch={"sub": _subdomain_option("sub", default="mail")}
    )
    assert service.get_url() == "https://mail.example.tld"


# --- is_enabled / is_installed / enable / disable ------------------------------------


def test_is_enabled_false_by_default(generic_userdata):
    service = _make_service()
    assert service.is_enabled() is False


def test_is_enabled_reads_userdata(generic_userdata):
    service = _make_service()
    with WriteUserData() as data:
        data.setdefault("modules", {}).setdefault("tsvc", {})["enable"] = True
    assert service.is_enabled() is True


def _patch_flake_manager(mocker, initial: dict | None = None) -> dict:
    """
    Patch FlakeServiceManager so that `async with FlakeServiceManager() as m: m.services`
    exposes a real dict we can inspect. Returns that dict.
    """
    services = initial if initial is not None else {}
    ctx_stub = MagicMock()
    ctx_stub.services = services
    ctx_stub.inputs = {
        "selfprivacy-nixos-config": {
            "url": "git+https://git.selfprivacy.org/SelfPrivacy/selfprivacy-nixos-config.git?ref=flakes"
        }
    }

    class FlakeManagerStub:
        async def __aenter__(self):
            return ctx_stub

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.FlakeServiceManager",
        return_value=FlakeManagerStub(),
    )
    return services


async def test_is_installed_true_when_service_in_flake_registry(mocker):
    _patch_flake_manager(mocker, {"tsvc": "some-flake-url"})
    service = _make_service()
    assert await service.is_installed() is True


async def test_is_installed_false_when_service_absent(mocker):
    _patch_flake_manager(mocker, {"other": "url"})
    service = _make_service()
    assert await service.is_installed() is False


async def test_disable_writes_false(generic_userdata):
    service = _make_service()
    service._set_enable(True)
    await service.disable()
    assert service.is_enabled() is False


def test_set_enable_creates_missing_paths(generic_userdata):
    service = _make_service()
    # Clear modules entirely first
    with WriteUserData() as data:
        data.pop("modules", None)
    service._set_enable(True)
    assert service.is_enabled() is True


async def test_enable_installed_skips_suggested_module_check(generic_userdata, mocker):
    flake_services = _patch_flake_manager(mocker, {"tsvc": "url"})
    exists_mock = mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=False
    )
    service = _make_service()
    await service.enable()
    # Because is_installed() short-circuits, we should never have checked the
    # suggested-modules path.
    assert not any(
        call.args and call.args[0] == SP_SUGGESTED_MODULES_PATH
        for call in exists_mock.call_args_list
    )
    assert flake_services == {"tsvc": "url"}
    assert service.is_enabled() is True


async def test_enable_missing_suggested_modules_file_raises(generic_userdata, mocker):
    _patch_flake_manager(mocker, {})
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=False)
    service = _make_service()
    with pytest.raises(FileNotFoundError):
        await service.enable()


async def test_enable_service_not_suggested_raises(generic_userdata, mocker, tmp_path):
    _patch_flake_manager(mocker, {})
    suggested_modules_path = tmp_path / "suggested-modules.json"
    suggested_modules_path.write_text(json.dumps(["other"]))
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.SP_SUGGESTED_MODULES_PATH",
        new=str(suggested_modules_path),
    )
    service = _make_service()
    with pytest.raises(ValueError, match="suggested"):
        await service.enable()


async def test_enable_registers_flake_and_sets_location(
    generic_userdata, mocker, tmp_path
):
    flake_services = _patch_flake_manager(mocker, {})
    suggested_modules_path = tmp_path / "suggested-modules.json"
    suggested_modules_path.write_text(json.dumps(["tsvc"]))
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.SP_SUGGESTED_MODULES_PATH",
        new=str(suggested_modules_path),
    )
    root_stub = MagicMock()
    root_stub.canonical_name = "sda1"
    block_devices_stub = MagicMock()
    block_devices_stub.get_root_block_device.return_value = root_stub
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.BlockDevices", return_value=block_devices_stub
    )

    service = _make_service(
        meta_patch={"isMovable": True},
        options_patch=_add_location_option({}),
    )
    await service.enable()

    assert "tsvc" in flake_services
    assert "sp-modules/tsvc" in flake_services["tsvc"]
    assert service.is_enabled() is True

    from selfprivacy_api.utils import ReadUserData

    with ReadUserData() as data:
        assert data["modules"]["tsvc"]["location"] == "sda1"


# --- Systemd wrappers ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_status_inactive_when_no_systemd_services():
    service = _make_service(meta_patch={"systemdServices": []})
    assert (await service.get_status()) == ServiceStatus.INACTIVE


@pytest.mark.asyncio
async def test_get_status_forwards_to_helper(mocker):
    async def fake(units):
        assert units == ["tsvc.service"]
        return ServiceStatus.ACTIVE

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.get_service_status_from_several_units",
        side_effect=fake,
    )
    service = _make_service()
    assert (await service.get_status()) == ServiceStatus.ACTIVE


@pytest.mark.asyncio
async def test_start_stop_restart_iterate_units(mocker):
    started, stopped, restarted = [], [], []

    async def fake_start(u):
        started.append(u)

    async def fake_stop(u):
        stopped.append(u)

    async def fake_restart(u):
        restarted.append(u)

    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.start_unit", side_effect=fake_start)
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.stop_unit", side_effect=fake_stop)
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.restart_unit", side_effect=fake_restart
    )

    service = _make_service(meta_patch={"systemdServices": ["a.service", "b.service"]})
    await service.start()
    await service.stop()
    await service.restart()

    assert started == ["a.service", "b.service"]
    assert stopped == ["a.service", "b.service"]
    assert restarted == ["a.service", "b.service"]


@pytest.mark.asyncio
async def test_wait_for_statuses_returns_immediately_when_already_matches(mocker):
    async def status_active(units):
        return ServiceStatus.ACTIVE

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.get_service_status_from_several_units",
        side_effect=status_active,
    )

    def never_yields(units):
        yield from ()

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.listen_for_unit_state_changes",
        side_effect=never_yields,
    )
    service = _make_service()
    # Should not block/iterate the async gen.
    await service.wait_for_statuses([ServiceStatus.ACTIVE])


@pytest.mark.asyncio
async def test_wait_for_statuses_polls_state_changes(mocker):
    statuses = iter(
        [ServiceStatus.INACTIVE, ServiceStatus.ACTIVATING, ServiceStatus.ACTIVE]
    )

    async def poll(units):
        return next(statuses)

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.get_service_status_from_several_units",
        side_effect=poll,
    )

    async def two_events(units):
        yield None
        yield None

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.listen_for_unit_state_changes",
        side_effect=two_events,
    )
    service = _make_service()
    await service.wait_for_statuses([ServiceStatus.ACTIVE])


# --- Configuration IO ----------------------------------------------------------------


def test_get_configuration_empty_when_no_items():
    service = _make_service()
    assert service.get_configuration() == {}


def test_get_configuration_returns_as_dict_payloads(generic_userdata):
    service = _make_service(
        options_patch={
            "flag": {
                "default": True,
                "description": "flag desc",
                "name": "flag",
                "meta": {"type": "bool", "weight": 2},
            }
        }
    )
    cfg = service.get_configuration()
    assert set(cfg.keys()) == {"flag"}
    assert cfg["flag"]["id"] == "flag"
    assert cfg["flag"]["value"] is True
    assert cfg["flag"]["type"] == "bool"


def test_set_configuration_rejects_unknown_key(generic_userdata):
    service = _make_service(
        options_patch={
            "flag": {
                "default": True,
                "description": "d",
                "name": "flag",
                "meta": {"type": "bool"},
            }
        }
    )
    with pytest.raises(ValueError, match="valid"):
        service.set_configuration({"nope": True})


def test_set_configuration_rejects_invalid_value(generic_userdata):
    service = _make_service(
        options_patch={
            "flag": {
                "default": True,
                "description": "d",
                "name": "flag",
                "meta": {"type": "bool"},
            }
        }
    )
    with pytest.raises(ValueError, match="not valid"):
        service.set_configuration({"flag": "not-a-bool"})


def test_set_configuration_delegates_to_config_items(generic_userdata):
    service = _make_service(
        options_patch={
            "flag": {
                "default": True,
                "description": "d",
                "name": "flag",
                "meta": {"type": "bool"},
            }
        }
    )
    service.set_configuration({"flag": False})
    assert service.get_configuration()["flag"]["value"] is False


# --- Storage, folders, drive ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_storage_usage_sums_across_folders(mocker):
    async def fake_size(folder):
        return {"a": 10, "b": 20, "c": 5}[folder]

    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.get_storage_usage", side_effect=fake_size
    )
    service = _make_service(meta_patch={"folders": ["a", "b", "c"]})
    assert (await service.get_storage_usage()) == 35


def test_has_folders_false_when_none_exist(tmpdir):
    service = _make_service(
        meta_patch={"folders": [str(tmpdir / "missing1"), str(tmpdir / "missing2")]}
    )
    assert service.has_folders() is False


def test_has_folders_true_when_any_exists(tmpdir):
    existing = tmpdir / "here"
    existing.mkdir()
    service = _make_service(
        meta_patch={"folders": [str(tmpdir / "missing"), str(existing)]}
    )
    assert service.has_folders() is True


def test_get_folders_merges_plain_and_owned():
    service = _make_service(
        meta_patch={
            "folders": ["/plain"],
            "ownedFolders": [{"path": "/owned", "owner": "tsvc", "group": "tsvc"}],
        }
    )
    assert service.get_folders() == ["/plain", "/owned"]


def test_get_owned_folders_wraps_plain_paths():
    service = _make_service(
        meta_patch={
            "folders": ["/plain"],
            "ownedFolders": [{"path": "/owned", "owner": "tsvc", "group": "tsvc"}],
        }
    )
    result = service.get_owned_folders()
    assert result[0] == OwnedPath(path="/owned", owner="tsvc", group="tsvc")
    # Plain folders are wrapped via owned_path() with service user/group defaults
    assert result[1] == OwnedPath(path="/plain", owner="tsvc", group="tsvc")


def test_get_folders_to_back_up_no_db():
    service = _make_service(meta_patch={"folders": ["/data"]})
    assert service.get_folders_to_back_up() == ["/data"]


def test_get_folders_to_back_up_appends_db_dumps_folder():
    service = _make_service(
        meta_patch={"folders": ["/data"], "postgreDatabases": ["main"]}
    )
    result = service.get_folders_to_back_up()
    assert result == ["/data", "/var/lib/postgresql-dumps/tsvc"]


def test_get_drive_non_movable_returns_root(mocker):
    root_stub = MagicMock()
    root_stub.canonical_name = "sda1"
    devices = MagicMock()
    devices.get_root_block_device.return_value = root_stub
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.BlockDevices", return_value=devices)
    service = _make_service()
    assert service.get_drive() == "sda1"


def test_get_drive_movable_reads_userdata_location(mocker, generic_userdata):
    root_stub = MagicMock()
    root_stub.canonical_name = "sda1"
    devices = MagicMock()
    devices.get_root_block_device.return_value = root_stub
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.BlockDevices", return_value=devices)

    service = _make_service(
        meta_patch={"isMovable": True},
        options_patch=_add_location_option({}),
    )
    with WriteUserData() as data:
        data["useBinds"] = True
        data.setdefault("modules", {}).setdefault("tsvc", {})["location"] = "sdb"
    assert service.get_drive() == "sdb"


def test_get_drive_movable_without_use_binds_returns_root(mocker, generic_userdata):
    root_stub = MagicMock()
    root_stub.canonical_name = "sda1"
    devices = MagicMock()
    devices.get_root_block_device.return_value = root_stub
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.BlockDevices", return_value=devices)

    service = _make_service(
        meta_patch={"isMovable": True},
        options_patch=_add_location_option({}),
    )
    with WriteUserData() as data:
        data["useBinds"] = False
        data.setdefault("modules", {}).setdefault("tsvc", {})["location"] = "sdb"
    assert service.get_drive() == "sda1"


def test_set_location_writes_userdata(generic_userdata):
    service = _make_service()
    volume = MagicMock()
    volume.name = "sdb"
    service.set_location(volume)

    from selfprivacy_api.utils import ReadUserData

    with ReadUserData() as data:
        assert data["modules"]["tsvc"]["location"] == "sdb"


# --- owned_path ----------------------------------------------------------------------


def test_owned_path_happy_path():
    service = _make_service()
    op = service.owned_path("/data")
    assert op == OwnedPath(path="/data", owner="tsvc", group="tsvc")


def test_owned_path_raises_when_user_missing():
    service = _make_service()
    service.get_user = lambda: None
    with pytest.raises(LookupError):
        service.owned_path("/data")


def test_owned_path_raises_when_group_missing():
    service = _make_service()
    service.get_group = lambda: None
    with pytest.raises(LookupError):
        service.owned_path("/data")


# --- DNS records ---------------------------------------------------------------------


def test_get_dns_records_no_subdomains_returns_empty(generic_userdata):
    service = _make_service()
    assert service.get_dns_records("1.2.3.4", "::1") == []


def test_get_dns_records_a_only_when_no_ip6(generic_userdata):
    service = _make_service(
        options_patch={"sub": _subdomain_option("sub", default="mail")}
    )
    records = service.get_dns_records("1.2.3.4", None)
    assert len(records) == 1
    assert records[0].type == "A"
    assert records[0].name == "mail"
    assert records[0].content == "1.2.3.4"
    assert records[0].display_name == "Test Service"


def test_get_dns_records_a_and_aaaa_per_subdomain(generic_userdata):
    service = _make_service(
        options_patch={
            "a": _subdomain_option("a", default="alpha"),
            "b": _subdomain_option("b", default="beta"),
        }
    )
    records = service.get_dns_records("1.2.3.4", "2001::1")
    assert [(r.type, r.name, r.content) for r in records] == [
        ("A", "alpha", "1.2.3.4"),
        ("AAAA", "alpha", "2001::1"),
        ("A", "beta", "1.2.3.4"),
        ("AAAA", "beta", "2001::1"),
    ]


def test_get_dns_records_skips_empty_subdomain_defaults(generic_userdata):
    service = _make_service(options_patch={"sub": _subdomain_option("sub", default="")})
    records = service.get_dns_records("1.2.3.4", "2001::1")
    assert records == []


# --- Backup / restore hooks ----------------------------------------------------------


def test_pre_backup_no_db_is_noop(mocker):
    dumper_ctor = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper")
    service = _make_service()
    service.pre_backup(job=MagicMock())
    dumper_ctor.assert_not_called()


def test_pre_backup_with_db_creates_folder_and_dumps(mocker):
    dumper_instance = MagicMock()
    dumper_ctor = mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper", return_value=dumper_instance
    )
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=False)
    mkdir_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.mkdir")
    jobs_update = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.Jobs.update")

    service = _make_service(meta_patch={"postgreDatabases": ["db1", "db2"]})
    job = MagicMock()
    service.pre_backup(job)

    mkdir_mock.assert_called_once_with("/var/lib/postgresql-dumps/tsvc")
    assert dumper_ctor.call_args_list == [
        mocker.call("db1"),
        mocker.call("db2"),
    ]
    assert dumper_instance.backup_database.call_args_list == [
        mocker.call("/var/lib/postgresql-dumps/tsvc/db1.dump"),
        mocker.call("/var/lib/postgresql-dumps/tsvc/db2.dump"),
    ]
    assert jobs_update.call_count == 2


def test_post_backup_removes_existing_dumps(mocker):
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=True)
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")
    service = _make_service(meta_patch={"postgreDatabases": ["db1"]})
    service.post_backup(job=MagicMock())
    remove_mock.assert_called_once_with("/var/lib/postgresql-dumps/tsvc/db1.dump")


def test_post_backup_skips_missing_dumps(mocker):
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=False)
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")
    service = _make_service(meta_patch={"postgreDatabases": ["db1"]})
    service.post_backup(job=MagicMock())
    remove_mock.assert_not_called()


def test_pre_restore_creates_folder_and_clears_dumps(mocker):
    dump_path = "/var/lib/postgresql-dumps/tsvc/db1.dump"
    # exists() is consulted for the folder (missing → mkdir) and then for the
    # dump file (present → remove).
    exists_present = {dump_path}
    mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.exists",
        side_effect=lambda path: path in exists_present,
    )
    mkdir_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.mkdir")
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")

    service = _make_service(meta_patch={"postgreDatabases": ["db1"]})
    service.pre_restore(job=MagicMock())

    mkdir_mock.assert_called_once_with("/var/lib/postgresql-dumps/tsvc")
    remove_mock.assert_called_once_with(dump_path)


@pytest.mark.asyncio
async def test_post_restore_restores_and_clears(mocker):
    dumper_instance = MagicMock()
    dumper_ctor = mocker.patch(
        f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper", return_value=dumper_instance
    )
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=True)
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.Jobs.update")

    service = _make_service(meta_patch={"postgreDatabases": ["db1"]})
    await service.post_restore(job=MagicMock())

    dumper_ctor.assert_called_once_with("db1")
    dumper_instance.restore_database.assert_called_once_with(
        "/var/lib/postgresql-dumps/tsvc/db1.dump"
    )
    # _clear_db_dumps runs after restore.
    assert remove_mock.called


@pytest.mark.asyncio
async def test_post_restore_raises_when_dump_missing(mocker):
    dumper_ctor = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper")
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.exists", return_value=False)
    mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")
    service = _make_service(meta_patch={"postgreDatabases": ["db1"]})
    with pytest.raises(FileNotFoundError):
        await service.post_restore(job=MagicMock())
    dumper_ctor.assert_not_called()


def test_backup_hooks_all_noop_without_databases(mocker):
    dumper_ctor = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper")
    mkdir_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.mkdir")
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")

    service = _make_service()
    service.pre_backup(job=MagicMock())
    service.post_backup(job=MagicMock())
    service.pre_restore(job=MagicMock())

    dumper_ctor.assert_not_called()
    mkdir_mock.assert_not_called()
    remove_mock.assert_not_called()


@pytest.mark.asyncio
async def test_post_restore_noop_without_databases(mocker):
    dumper_ctor = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.PostgresDumper")
    mkdir_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.mkdir")
    remove_mock = mocker.patch(f"{TEMPLATED_SERVICE_MODULE_PATH}.remove")

    service = _make_service()
    await service.post_restore(job=MagicMock())

    dumper_ctor.assert_not_called()
    mkdir_mock.assert_not_called()
    remove_mock.assert_not_called()
