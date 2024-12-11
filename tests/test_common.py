# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import os
import pytest
from typing import Optional

from selfprivacy_api.utils import WriteUserData, ReadUserData, get_test_mode


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


# TODO: Does it make any sense to have such a fixture though?
# If it can only be called from tests then it is always test
@pytest.fixture
def test_mode():
    return get_test_mode()


def test_the_test_mode(test_mode):
    assert test_mode == "true"
