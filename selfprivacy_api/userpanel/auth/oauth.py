from authlib.integrations.starlette_client import OAuth

from selfprivacy_api.utils.oauth_secrets import (
    load_oauth_client_secret,
    OAUTH_CLIENT_ID,
)
from selfprivacy_api.utils import get_domain

_chached_oauth = None


def get_oauth():
    global _chached_oauth

    if _chached_oauth is not None:
        return _chached_oauth

    _chached_oauth = OAuth()

    idm_domain_url = f"https://auth.{get_domain()}"

    _chached_oauth.register(
        name="kanidm",
        client_id=OAUTH_CLIENT_ID,
        client_secret=load_oauth_client_secret(),
        server_metadata_url=(
            f"{idm_domain_url}/oauth2/openid/{OAUTH_CLIENT_ID}/.well-known/openid-configuration"
        ),
        client_kwargs={
            "scope": "openid profile email groups",
            "code_challenge_method": "S256",
            "token_endpoint_auth_method": "client_secret_post",
        },
        userinfo_endpoint=f"{idm_domain_url}/oauth2/openid/{OAUTH_CLIENT_ID}/userinfo",
    )

    return _chached_oauth
