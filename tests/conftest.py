import pytest
from flask import testing
from selfprivacy_api.app import create_app


@pytest.fixture
def tokens_file(mocker, shared_datadir):
    mock = mocker.patch(
        "selfprivacy_api.utils.TOKENS_FILE", shared_datadir / "tokens.json"
    )
    return mock


@pytest.fixture
def app():
    app = create_app(
        {
            "ENABLE_SWAGGER": "1",
        }
    )

    yield app


@pytest.fixture
def client(app, tokens_file):
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


class WrongAuthClient(testing.FlaskClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = "WRONG_TOKEN"

    def open(self, *args, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
        return super().open(*args, **kwargs)


@pytest.fixture
def authorized_client(app, tokens_file):
    app.test_client_class = AuthorizedClient
    return app.test_client()


@pytest.fixture
def wrong_auth_client(app, tokens_file):
    app.test_client_class = WrongAuthClient
    return app.test_client()


@pytest.fixture
def runner(app, tokens_file):
    return app.test_cli_runner()
