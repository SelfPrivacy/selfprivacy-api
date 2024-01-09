import pytest

from selfprivacy_api.migrations.modules_in_json import CreateModulesField
from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.services import get_all_services


@pytest.fixture()
def stray_services(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=datadir / "strays.json")
    return datadir


@pytest.fixture()
def empty_json(generic_userdata):
    with WriteUserData() as data:
        data.clear()

    with ReadUserData() as data:
        assert len(data.keys()) == 0

    return


def test_modules_empty_json(empty_json):
    with ReadUserData() as data:
        assert "modules" not in data.keys()

    assert CreateModulesField().is_migration_needed()

    CreateModulesField().migrate()
    assert not CreateModulesField().is_migration_needed()

    with ReadUserData() as data:
        assert "modules" in data.keys()


@pytest.mark.parametrize("modules_field", [True, False])
def test_modules_stray_services(modules_field, stray_services):
    if not modules_field:
        with WriteUserData() as data:
            del data["modules"]
    assert CreateModulesField().is_migration_needed()

    CreateModulesField().migrate()

    for service in get_all_services():
        # assumes we do not tolerate previous format
        assert service.is_enabled()
        if service.get_id() == "email":
            continue
        with ReadUserData() as data:
            assert service.get_id() in data["modules"].keys()
            assert service.get_id() not in data.keys()

    assert not CreateModulesField().is_migration_needed()


def test_modules_no_migration_on_generic_data(generic_userdata):
    assert not CreateModulesField().is_migration_needed()
