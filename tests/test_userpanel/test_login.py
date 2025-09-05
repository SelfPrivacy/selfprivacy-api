import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse
from starlette.responses import Response as StarletteResponse

from selfprivacy_api.userpanel.routes.login import router as login_router


class FakeKanidm:
    def __init__(self):
        self.token = {"userinfo": {"preferred_username": "tester"}}

    async def authorize_redirect(self, request, redirect_uri: str):
        return RedirectResponse(
            url=f"https://test.domain/authorize?redirect_uri={redirect_uri}"
        )

    async def authorize_access_token(self, request):
        return self.token


class _OAuthRegistry:
    def __init__(self, client: FakeKanidm):
        self._client = client

    def create_client(self, name: str):
        return self._client if name == "kanidm" else None


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(login_router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def kanidm_oauth_mock(mocker):
    fake = FakeKanidm()
    mocker.patch(
        "selfprivacy_api.userpanel.routes.login.get_oauth",
        autospec=True,
        return_value=_OAuthRegistry(fake),
    )
    return fake


@pytest.fixture
def session_stubs(mocker):
    mocker.patch(
        "selfprivacy_api.userpanel.routes.login.generate_session_token",
        autospec=True,
        return_value="token123",
    )

    async def fake_create_session(session_token, username):
        return SimpleNamespace(
            expires_at=datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)
        )

    mocker.patch(
        "selfprivacy_api.userpanel.routes.login.create_session",
        autospec=True,
        side_effect=fake_create_session,
    )

    set_cookie_mock = mocker.patch(
        "selfprivacy_api.userpanel.routes.login.set_session_token_cookie",
        autospec=True,
    )
    return set_cookie_mock


def test_login_via_kanidm_redirects_to_provider(client, kanidm_oauth_mock):
    resp = client.get("/oauth", follow_redirects=False)

    assert resp.status_code == 307
    expected_redirect_uri = f"{client.base_url}/callback"
    assert resp.headers["location"] == (
        f"https://test.domain/authorize?redirect_uri={expected_redirect_uri}"
    )


def test_auth_via_kanidm_success_sets_cookie_and_redirects(
    client, kanidm_oauth_mock, session_stubs
):
    resp = client.get("/callback", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == "/user"

    assert session_stubs.call_count == 1
    response_arg, token_arg, expires_at_arg = session_stubs.call_args[0]

    assert isinstance(response_arg, StarletteResponse)
    assert token_arg == "token123"
    assert isinstance(expires_at_arg, datetime.datetime)
    assert expires_at_arg.year == 2030
