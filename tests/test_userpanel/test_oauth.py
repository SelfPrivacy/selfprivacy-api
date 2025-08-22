import pytest

from selfprivacy_api.userpanel.auth.oauth import get_oauth

from authlib.integrations.starlette_client import OAuth


@pytest.fixture
def get_domain_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.userpanel.auth.oauth.get_domain",
        autospec=True,
        return_value="test.domain",
    )
    return mock


@pytest.fixture
def load_oauth_client_secret_mock(mocker):
    mock = mocker.patch(
        "selfprivacy_api.userpanel.auth.oauth.load_oauth_client_secret",
        autospec=True,
        return_value="tsss-its-a-secret",
    )
    return mock


def test_get_oauth(get_domain_mock, load_oauth_client_secret_mock):
    assert isinstance(get_oauth(), OAuth)
