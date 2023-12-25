"""
    Tests for generic service methods
"""
import pytest
from pytest import raises

from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.waitloop import wait_until_true

from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.generic_service_mover import FolderMoveNames

from selfprivacy_api.services.test_service import DummyService
from selfprivacy_api.services.service import Service, ServiceStatus, StoppedService


def test_unimplemented_folders_raises():
    with raises(NotImplementedError):
        Service.get_folders()
    with raises(NotImplementedError):
        Service.get_owned_folders()

    class OurDummy(DummyService, folders=["testydir", "dirtessimo"]):
        pass

    owned_folders = OurDummy.get_owned_folders()
    assert owned_folders is not None


def test_service_stopper(raw_dummy_service):
    dummy: Service = raw_dummy_service
    dummy.set_delay(0.3)

    assert dummy.get_status() == ServiceStatus.ACTIVE

    with StoppedService(dummy) as stopped_dummy:
        assert stopped_dummy.get_status() == ServiceStatus.INACTIVE
        assert dummy.get_status() == ServiceStatus.INACTIVE

    assert dummy.get_status() == ServiceStatus.ACTIVE


def test_delayed_start_stop(raw_dummy_service):
    dummy = raw_dummy_service
    dummy.set_delay(0.3)

    dummy.stop()
    assert dummy.get_status() == ServiceStatus.DEACTIVATING
    wait_until_true(lambda: dummy.get_status() == ServiceStatus.INACTIVE)
    assert dummy.get_status() == ServiceStatus.INACTIVE

    dummy.start()
    assert dummy.get_status() == ServiceStatus.ACTIVATING
    wait_until_true(lambda: dummy.get_status() == ServiceStatus.ACTIVE)
    assert dummy.get_status() == ServiceStatus.ACTIVE


def test_owned_folders_from_not_owned():
    assert Bitwarden.get_owned_folders() == [
        OwnedPath(
            path=folder,
            group="vaultwarden",
            owner="vaultwarden",
        )
        for folder in Bitwarden.get_folders()
    ]


def test_paths_from_owned_paths():
    assert len(Pleroma.get_folders()) == 2
    assert Pleroma.get_folders() == [
        ownedpath.path for ownedpath in Pleroma.get_owned_folders()
    ]


def test_foldermoves_from_ownedpaths():
    owned = OwnedPath(
        path="var/lib/bitwarden",
        group="vaultwarden",
        owner="vaultwarden",
    )

    assert FolderMoveNames.from_owned_path(owned) == FolderMoveNames(
        name="bitwarden",
        bind_location="var/lib/bitwarden",
        group="vaultwarden",
        owner="vaultwarden",
    )


def test_enabling_disabling_reads_json(dummy_service: DummyService):
    with WriteUserData() as data:
        data[dummy_service.get_id()]["enable"] = False
    assert dummy_service.is_enabled() is False
    with WriteUserData() as data:
        data[dummy_service.get_id()]["enable"] = True
    assert dummy_service.is_enabled() is True


@pytest.fixture(params=["normally_enabled", "deleted_attribute", "service_not_in_json"])
def possibly_dubiously_enabled_service(
    dummy_service: DummyService, request
) -> DummyService:
    if request.param == "deleted_attribute":
        with WriteUserData() as data:
            del data[dummy_service.get_id()]["enable"]
    if request.param == "service_not_in_json":
        with WriteUserData() as data:
            del data[dummy_service.get_id()]
    return dummy_service


# Yeah, idk yet how to dry it.
@pytest.fixture(params=["deleted_attribute", "service_not_in_json"])
def undefined_enabledness_service(dummy_service: DummyService, request) -> DummyService:
    if request.param == "deleted_attribute":
        with WriteUserData() as data:
            del data[dummy_service.get_id()]["enable"]
    if request.param == "service_not_in_json":
        with WriteUserData() as data:
            del data[dummy_service.get_id()]
    return dummy_service


def test_undefined_enabledness_in_json_means_False(
    undefined_enabledness_service: DummyService,
):
    dummy_service = undefined_enabledness_service
    assert dummy_service.is_enabled() is False


def test_enabling_disabling_writes_json(
    possibly_dubiously_enabled_service: DummyService,
):
    dummy_service = possibly_dubiously_enabled_service

    dummy_service.disable()
    with ReadUserData() as data:
        assert data[dummy_service.get_id()]["enable"] is False
    dummy_service.enable()
    with ReadUserData() as data:
        assert data[dummy_service.get_id()]["enable"] is True
    dummy_service.disable()
    with ReadUserData() as data:
        assert data[dummy_service.get_id()]["enable"] is False
