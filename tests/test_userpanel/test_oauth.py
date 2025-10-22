import pytest

from selfprivacy_api.userpanel.auth.oauth import get_oauth

from authlib.integrations.starlette_client import OAuth

TEST_CLIENT_SECRET = "tsss-its-a-secret"


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
        return_value=TEST_CLIENT_SECRET,
    )
    return mock


def test_get_oauth(get_domain_mock, load_oauth_client_secret_mock):
    oauth = get_oauth()

    assert isinstance(oauth, OAuth)
    assert "kanidm" in oauth._clients

    client = oauth._clients["kanidm"]
    assert client.client_secret == TEST_CLIENT_SECRET
