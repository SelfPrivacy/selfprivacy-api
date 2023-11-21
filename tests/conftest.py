"""Tests configuration."""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest
from os import path

from fastapi.testclient import TestClient
import os.path as path
import datetime

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)

from tests.common import read_json

EMPTY_TOKENS_JSON = ' {"tokens": []}'


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
def tokens_file(empty_redis_repo, tmpdir):
    """A state with tokens"""
    repo = empty_redis_repo
    for token in TOKENS_FILE_CONTENTS["tokens"]:
        repo._store_token(
            Token(
                token=token["token"],
                device_name=token["name"],
                created_at=token["date"],
            )
        )
    return repo


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
def huey_database(mocker, shared_datadir):
    """Mock huey database."""
    mock = mocker.patch(
        "selfprivacy_api.utils.huey.HUEY_DATABASE", shared_datadir / "huey.db"
    )
    return mock


@pytest.fixture
def client(tokens_file, huey_database):
    from selfprivacy_api.app import app

    return TestClient(app)


@pytest.fixture
def authorized_client(tokens_file, huey_database):
    """Authorized test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update(
        {"Authorization": "Bearer " + DEVICE_WE_AUTH_TESTS_WITH["token"]}
    )
    return client


@pytest.fixture
def wrong_auth_client(tokens_file, huey_database):
    """Wrong token test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer WRONG_TOKEN"})
    return client
