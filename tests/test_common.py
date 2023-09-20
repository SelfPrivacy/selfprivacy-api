# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import os
import pytest

from selfprivacy_api.utils import WriteUserData, ReadUserData

from os import path
from os import makedirs
from typing import Generator

# import pickle
import selfprivacy_api.services as services
from selfprivacy_api.services import get_service_by_id, Service
from selfprivacy_api.services.test_service import DummyService


TESTFILE_BODY = "testytest!"
TESTFILE_2_BODY = "testissimo!"


@pytest.fixture()
def raw_dummy_service(tmpdir):
    dirnames = ["test_service", "also_test_service"]
    service_dirs = []
    for d in dirnames:
        service_dir = path.join(tmpdir, d)
        makedirs(service_dir)
        service_dirs.append(service_dir)

    testfile_path_1 = path.join(service_dirs[0], "testfile.txt")
    with open(testfile_path_1, "w") as file:
        file.write(TESTFILE_BODY)

    testfile_path_2 = path.join(service_dirs[1], "testfile2.txt")
    with open(testfile_path_2, "w") as file:
        file.write(TESTFILE_2_BODY)

    # we need this to not change get_folders() much
    class TestDummyService(DummyService, folders=service_dirs):
        pass

    service = TestDummyService()
    # assert pickle.dumps(service) is not None
    return service


@pytest.fixture()
def dummy_service(tmpdir, raw_dummy_service) -> Generator[Service, None, None]:
    service = raw_dummy_service

    # register our service
    services.services.append(service)

    assert get_service_by_id(service.get_id()) is not None
    yield service

    # cleanup because apparently it matters wrt tasks
    services.services.remove(service)


def test_get_api_version(authorized_client):
    response = authorized_client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_get_api_version_unauthorized(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_read_invalid_user_data():
    with pytest.raises(ValueError):
        with ReadUserData("invalid") as user_data:
            pass


def test_write_invalid_user_data():
    with pytest.raises(ValueError):
        with WriteUserData("invalid") as user_data:
            pass


@pytest.fixture
def test_mode():
    return os.environ.get("TEST_MODE")


def test_the_test_mode(test_mode):
    assert test_mode == "true"
