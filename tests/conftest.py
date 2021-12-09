import pytest
from flask import testing
from selfprivacy_api.app import create_app


@pytest.fixture
def app():
    app = create_app(
        {
            "AUTH_TOKEN": "TEST_TOKEN",
            "ENABLE_SWAGGER": "0",
        }
    )

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class AuthorizedClient(testing.FlaskClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = "TEST_TOKEN"

    def open(self, *args, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
        return super().open(*args, **kwargs)


@pytest.fixture
def authorized_client(app):
    app.test_client_class = AuthorizedClient
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
