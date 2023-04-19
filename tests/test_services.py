"""
    Tests for generic service methods
"""
from pytest import raises

from selfprivacy_api.services.bitwarden import Bitwarden
from selfprivacy_api.services.pleroma import Pleroma
from selfprivacy_api.services.owned_path import OwnedPath
from selfprivacy_api.services.generic_service_mover import FolderMoveNames

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
