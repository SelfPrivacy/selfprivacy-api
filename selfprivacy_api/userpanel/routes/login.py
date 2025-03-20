from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from authlib.integrations.starlette_client import OAuth
from selfprivacy_api.utils.oauth_secrets import (
    load_oauth_client_secret,
    OAUTH_CLIENT_ID,
)
from selfprivacy_api.utils import get_domain
import logging

import sys
log = logging.getLogger('authlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)

router = APIRouter()

logger = logging.getLogger(__name__)

oauth = OAuth()

idm_domain = f"https://auth.{get_domain()}"
client_secret = load_oauth_client_secret()

logger.info(f"This is the client secret from the global scope: {client_secret}")

oauth.register(
    name="kanidm",
    client_id=OAUTH_CLIENT_ID,
    client_secret=client_secret,
    server_metadata_url=f"{idm_domain}/oauth2/openid/{OAUTH_CLIENT_ID}/.well-known/openid-configuration",
    # access_token_url=f"{idm_domain}/oauth2/token",
    # access_token_params=None,
    # authorize_url=f"{idm_domain}/ui/oauth2",
    # authorize_params=None,
    client_kwargs={
        "scope": "openid profile email groups",
        "code_challenge_method": "S256",
        'token_endpoint_auth_method': 'client_secret_post',
    },
    userinfo_endpoint=f"{idm_domain}/oauth2/openid/{OAUTH_CLIENT_ID}/userinfo",
)


@router.route("/")
async def login_via_kanidm(request: Request):
    logger.info(f"Logging in via kanidm. The client secret is: {client_secret}")
    kanidm = oauth.create_client("kanidm")
    if not kanidm:
        logger.error("Kanidm not found in oauth clients")
        raise HTTPException(status_code=500)
    redirect_uri = request.url_for("auth_via_kanidm")
    return await kanidm.authorize_redirect(request, redirect_uri)


@router.route("/callback")
async def auth_via_kanidm(request: Request):
    kanidm = oauth.create_client("kanidm")
    if not kanidm:
        logger.error("Kanidm not found in oauth clients")
        raise HTTPException(status_code=500)
    token = await kanidm.authorize_access_token(request)
    logger.info(f"Token: {token}")
    logger.info(f"User info: {dict(token['userinfo'])}")

    return {"detail": "Logged in via kanidm"}
