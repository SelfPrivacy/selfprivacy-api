"""Tests configuration."""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest
from fastapi.testclient import TestClient
import os.path as path
import datetime

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
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
def empty_tokens(mocker, tmpdir):
    tokenfile = tmpdir / "empty_tokens.json"
    with open(tokenfile, "w") as file:
        file.write(EMPTY_TOKENS_JSON)
    mocker.patch("selfprivacy_api.utils.TOKENS_FILE", new=tokenfile)
    assert read_json(tokenfile)["tokens"] == []
    return tmpdir


@pytest.fixture
def empty_json_repo(empty_tokens):
    repo = JsonTokensRepository()
    for token in repo.get_tokens():
        repo.delete_token(token)
    assert repo.get_tokens() == []
    return repo


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
def jobs_file(mocker, shared_datadir):
    """Mock tokens file."""
    mock = mocker.patch("selfprivacy_api.utils.JOBS_FILE", shared_datadir / "jobs.json")
    return mock


@pytest.fixture
def huey_database(mocker, shared_datadir):
    """Mock huey database."""
    mock = mocker.patch(
        "selfprivacy_api.utils.huey.HUEY_DATABASE", shared_datadir / "huey.db"
    )
    return mock


@pytest.fixture
def client(tokens_file, huey_database, jobs_file):
    from selfprivacy_api.app import app

    return TestClient(app)


@pytest.fixture
def authorized_client(tokens_file, huey_database, jobs_file):
    """Authorized test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update(
        {"Authorization": "Bearer " + DEVICE_WE_AUTH_TESTS_WITH["token"]}
    )
    return client


@pytest.fixture
def wrong_auth_client(tokens_file, huey_database, jobs_file):
    """Wrong token test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer WRONG_TOKEN"})
    return client
