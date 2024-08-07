"""Tests configuration."""

# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest
import datetime
import subprocess

from os import path
from os import makedirs
from typing import Generator
from fastapi.testclient import TestClient
from selfprivacy_api.models.tokens.token import Token

from selfprivacy_api.utils.huey import huey

import selfprivacy_api.services as services
from selfprivacy_api.services import get_service_by_id, Service
from selfprivacy_api.services.test_service import DummyService

from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)


TESTFILE_BODY = "testytest!"
TESTFILE_2_BODY = "testissimo!"

TOKENS_FILE_CONTENTS = {
    "tokens": [
        {
            "token": "TEST_TOKEN",
            "name": "test_token",
            "date": datetime.datetime(2022, 1, 14, 8, 31, 10, 789314),
        },
        {
            "token": "TEST_TOKEN2",
            "name": "test_token2",
            "date": datetime.datetime(2022, 1, 14, 8, 31, 10, 789314),
        },
    ]
}

TOKENS = [
    Token(
        token="TEST_TOKEN",
        device_name="test_token",
        created_at=datetime.datetime(2022, 1, 14, 8, 31, 10, 789314),
    ),
    Token(
        token="TEST_TOKEN2",
        device_name="test_token2",
        created_at=datetime.datetime(2022, 1, 14, 8, 31, 10, 789314),
    ),
]

DEVICE_WE_AUTH_TESTS_WITH = TOKENS_FILE_CONTENTS["tokens"][0]


def pytest_generate_tests(metafunc):
    os.environ["TEST_MODE"] = "true"


def global_data_dir():
    return path.join(path.dirname(__file__), "data")


@pytest.fixture
def empty_redis_repo():
    repo = RedisTokensRepository()
    repo.reset()
    assert repo.get_tokens() == []
    return repo


@pytest.fixture
def redis_repo_with_tokens():
    repo = RedisTokensRepository()
    repo.reset()
    for token in TOKENS:
        repo._store_token(token)
    assert sorted(repo.get_tokens(), key=lambda x: x.token) == sorted(
        TOKENS, key=lambda x: x.token
    )


@pytest.fixture
def generic_userdata(mocker, tmpdir):
    filename = "turned_on.json"
    source_path = path.join(global_data_dir(), filename)
    userdata_path = path.join(tmpdir, filename)

    with open(userdata_path, "w") as file:
        with open(source_path, "r") as source:
            file.write(source.read())

    mock = mocker.patch("selfprivacy_api.utils.USERDATA_FILE", new=userdata_path)
    return mock


@pytest.fixture
def client(redis_repo_with_tokens):
    from selfprivacy_api.app import app

    return TestClient(app)


@pytest.fixture
def authorized_client(redis_repo_with_tokens):
    """Authorized test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update(
        {"Authorization": "Bearer " + DEVICE_WE_AUTH_TESTS_WITH["token"]}
    )
    return client


@pytest.fixture
def wrong_auth_client(redis_repo_with_tokens):
    """Wrong token test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer WRONG_TOKEN"})
    return client


@pytest.fixture()
def volume_folders(tmpdir, mocker):
    volumes_dir = path.join(tmpdir, "volumes")

    makedirs(volumes_dir)
    volumenames = ["sda1", "sda2"]
    for d in volumenames:
        service_dir = path.join(volumes_dir, d)
        makedirs(service_dir)
    mock = mocker.patch("selfprivacy_api.services.owned_path.VOLUMES_PATH", volumes_dir)


@pytest.fixture()
def raw_dummy_service(tmpdir) -> DummyService:
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


def ensure_user_exists(user: str):
    try:
        output = subprocess.check_output(
            ["useradd", "-U", user], stderr=subprocess.PIPE, shell=False
        )
    except subprocess.CalledProcessError as error:
        if b"already exists" not in error.stderr:
            raise error

    try:
        output = subprocess.check_output(
            ["useradd", user], stderr=subprocess.PIPE, shell=False
        )
    except subprocess.CalledProcessError as error:
        assert b"already exists" in error.stderr
        return

    raise ValueError("could not create user", user)


@pytest.fixture()
def dummy_service(
    tmpdir, raw_dummy_service, generic_userdata
) -> Generator[Service, None, None]:
    service = raw_dummy_service
    user = service.get_user()

    # TODO: use create_user from users actions. But it will need NIXOS to be there
    # and react to our changes to files.
    # from selfprivacy_api.actions.users import create_user
    # create_user(user, "yay, it is me")
    ensure_user_exists(user)

    # register our service
    services.services.append(service)

    huey.immediate = True
    assert huey.immediate is True

    assert get_service_by_id(service.get_id()) is not None
    service.enable()
    yield service

    # Cleanup because apparently it matters wrt tasks
    # Some tests may remove it from the list intentionally, this is fine
    if service in services.services:
        services.services.remove(service)
