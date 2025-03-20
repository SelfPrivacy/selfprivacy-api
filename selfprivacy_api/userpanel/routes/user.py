from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from selfprivacy_api.userpanel.templates import templates
from selfprivacy_api.userpanel.auth.session import Session, delete_session_token_cookie
from selfprivacy_api.userpanel.routes.dependencies import get_current_user
from typing import Annotated

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_profile(
    request: Request, user: Annotated[Session, Depends(get_current_user)]
):
    logger.info(f"User {user}")
    return templates.TemplateResponse(
        "profile.html", {"request": request, "username": user.user_id}
    )


@router.get("/logout")
async def logout(request: Request, user: Annotated[Session, Depends(get_current_user)]):
    response = RedirectResponse(url="/login")
    delete_session_token_cookie(response)
    return response
