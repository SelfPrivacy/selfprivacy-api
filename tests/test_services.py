"""
    Tests for generic service methods
"""
import pytest
from pytest import raises

from selfprivacy_api.utils import ReadUserData, WriteUserData
from selfprivacy_api.utils.waitloop import wait_until_true

import selfprivacy_api.services as services_module

from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.mailserver import MailServer
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.generic_service_mover import FolderMoveNames

from selfprivacy_api.services.test_service import DummyService
from selfprivacy_api.services.service import Service, ServiceStatus, StoppedService
from selfprivacy_api.services import get_enabled_services

from tests.test_dkim import dkim_file, no_dkim_file


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
        data["modules"][dummy_service.get_id()]["enable"] = False
    assert dummy_service.is_enabled() is False
    with WriteUserData() as data:
        data["modules"][dummy_service.get_id()]["enable"] = True
    assert dummy_service.is_enabled() is True


# A helper to test undefined states. Used in fixtures below
def undefine_service_enabled_status(param, dummy_service):
    if param == "deleted_attribute":
        with WriteUserData() as data:
            del data["modules"][dummy_service.get_id()]["enable"]
    if param == "service_not_in_json":
        with WriteUserData() as data:
            del data["modules"][dummy_service.get_id()]
    if param == "modules_not_in_json":
        with WriteUserData() as data:
            del data["modules"]


# May be defined or not
@pytest.fixture(
    params=[
        "normally_enabled",
        "deleted_attribute",
        "service_not_in_json",
        "modules_not_in_json",
    ]
)
def possibly_dubiously_enabled_service(
    dummy_service: DummyService, request
) -> DummyService:
    if request.param != "normally_enabled":
        undefine_service_enabled_status(request.param, dummy_service)
    return dummy_service


# Strictly UNdefined
@pytest.fixture(
    params=["deleted_attribute", "service_not_in_json", "modules_not_in_json"]
)
def undefined_enabledness_service(dummy_service: DummyService, request) -> DummyService:
    undefine_service_enabled_status(request.param, dummy_service)
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
        assert data["modules"][dummy_service.get_id()]["enable"] is False
    dummy_service.enable()
    with ReadUserData() as data:
        assert data["modules"][dummy_service.get_id()]["enable"] is True
    dummy_service.disable()
    with ReadUserData() as data:
        assert data["modules"][dummy_service.get_id()]["enable"] is False


# more detailed testing of this is in test_graphql/test_system.py
def test_mailserver_with_dkim_returns_some_dns(dkim_file):
    records = MailServer().get_dns_records("203.0.113.3", "2001:db8::1")
    assert len(records) > 0


def test_mailserver_with_no_dkim_returns_no_dns(no_dkim_file):
    assert MailServer().get_dns_records("203.0.113.3", "2001:db8::1") == []


def test_services_enabled_by_default(generic_userdata):
    assert set(get_enabled_services()) == set(services_module.services)
