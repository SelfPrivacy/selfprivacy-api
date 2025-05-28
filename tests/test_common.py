# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest

from selfprivacy_api.utils import WriteUserData, ReadUserData


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


def inspect_file(path: str):
    with open(path) as file:
        raise ValueError(file.read())
