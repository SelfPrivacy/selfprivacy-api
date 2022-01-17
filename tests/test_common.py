# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
import json
import pytest


def test_get_api_version(authorized_client):
    response = authorized_client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.get_json()


def test_get_api_version_unauthorized(client):
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.get_json()

def test_get_swagger_json(authorized_client):
    response = authorized_client.get("/api/swagger.json")
    assert response.status_code == 200
    assert "swagger" in response.get_json()
