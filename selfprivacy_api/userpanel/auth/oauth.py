from authlib.integrations.starlette_client import OAuth
from selfprivacy_api.utils.oauth_secrets import (
    load_oauth_client_secret,
    OAUTH_CLIENT_ID,
)
from selfprivacy_api.utils import get_domain

oauth = OAuth()

idm_domain = f"https://auth.{get_domain()}"

oauth.register(
    name="kanidm",
    client_id=OAUTH_CLIENT_ID,
    client_secret=load_oauth_client_secret(),
    server_metadata_url=f"{idm_domain}/oauth2/openid/{OAUTH_CLIENT_ID}/.well-known/openid-configuration",
    # access_token_url=f"{idm_domain}/oauth2/token",
    # access_token_params=None,
    # authorize_url=f"{idm_domain}/ui/oauth2",
    # authorize_params=None,
    client_kwargs={
        "scope": "openid profile email groups",
        "code_challenge_method": "S256",
        "token_endpoint_auth_method": "client_secret_post",
    },
    userinfo_endpoint=f"{idm_domain}/oauth2/openid/{OAUTH_CLIENT_ID}/userinfo",
)
