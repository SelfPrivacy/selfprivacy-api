import logging

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.requests import Request
from authlib.integrations.base_client.errors import OAuthError

from selfprivacy_api.userpanel.templates import templates
from selfprivacy_api.userpanel.auth.oauth import get_oauth
from selfprivacy_api.userpanel.auth.session import (
    generate_session_token,
    create_session,
    set_session_token_cookie,
)


router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/oauth")
async def login_via_kanidm(request: Request):
    kanidm = get_oauth().create_client("kanidm")
    if not kanidm:
        logger.error("Kanidm not found in oauth clients")
        raise HTTPException(status_code=500)
    redirect_uri = request.url_for("auth_via_kanidm")
    return await kanidm.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_via_kanidm(request: Request, response: Response):
    kanidm = get_oauth().create_client("kanidm")
    if not kanidm:
        logger.error("Kanidm not found in oauth clients")
        raise HTTPException(status_code=500)
    try:
        token = await kanidm.authorize_access_token(request)
    except OAuthError as e:
        logger.error(f"Error getting token from kanidm: {e}")
        raise HTTPException(status_code=400, detail="Invalid authorization request")
    except Exception as e:
        logger.error(f"Error getting token from kanidm: {e}")
        raise HTTPException(status_code=500)

    if not token:
        logger.error("No token received from kanidm")
        raise HTTPException(status_code=500)

    username = token.get("userinfo", {}).get("preferred_username")

    if not username:
        logger.error("No username found in token")
        raise HTTPException(status_code=500)

    session_token = generate_session_token()
    session = await create_session(
        session_token,
        username,
    )

    response = RedirectResponse(url="/user")

    set_session_token_cookie(response, session_token, session.expires_at)

    return response
