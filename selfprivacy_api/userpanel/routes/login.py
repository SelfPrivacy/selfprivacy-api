from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from selfprivacy_api.userpanel.auth.ouath import oauth
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.route("/")
async def login_via_kanidm(request: Request):
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
