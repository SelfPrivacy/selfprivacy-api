"""
    Tests for generic service methods
"""
from pytest import raises

from selfprivacy_api.services.test_service import DummyService
from selfprivacy_api.services.service import Service


def test_unimplemented_folders_raises():
    with raises(NotImplementedError):
        Service.get_folders()
    with raises(NotImplementedError):
        Service.get_owned_folders()

    class OurDummy(DummyService, folders=["testydir", "dirtessimo"]):
        pass

    owned_folders = OurDummy.get_owned_folders()
    assert owned_folders is not None
