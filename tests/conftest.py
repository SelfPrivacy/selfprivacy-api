"""Tests configuration."""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest
from os import path

from fastapi.testclient import TestClient


def pytest_generate_tests(metafunc):
    os.environ["TEST_MODE"] = "true"


def global_data_dir():
    return path.join(path.dirname(__file__), "data")


@pytest.fixture
def tokens_file(mocker, shared_datadir):
    """Mock tokens file."""
    mock = mocker.patch(
        "selfprivacy_api.utils.TOKENS_FILE", shared_datadir / "tokens.json"
    )
    return mock


@pytest.fixture
def jobs_file(mocker, shared_datadir):
    """Mock tokens file."""
    mock = mocker.patch("selfprivacy_api.utils.JOBS_FILE", shared_datadir / "jobs.json")
    return mock


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
def client(tokens_file, huey_database, jobs_file):
    from selfprivacy_api.app import app

    return TestClient(app)


@pytest.fixture
def authorized_client(tokens_file, huey_database, jobs_file):
    """Authorized test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer TEST_TOKEN"})
    return client


@pytest.fixture
def wrong_auth_client(tokens_file, huey_database, jobs_file):
    """Wrong token test client fixture."""
    from selfprivacy_api.app import app

    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer WRONG_TOKEN"})
    return client
