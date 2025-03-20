from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from selfprivacy_api.models.user import UserDataUser
from selfprivacy_api.userpanel.templates import templates
from selfprivacy_api.userpanel.auth.session import Session, delete_session_token_cookie
from selfprivacy_api.userpanel.routes.dependencies import get_current_user
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)
from typing import Annotated

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def get_profile(
    request: Request, session: Annotated[Session, Depends(get_current_user)]
):
    try:
        user: UserDataUser = KanidmUserRepository.get_user_by_username(session.user_id)
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise HTTPException(status_code=500)
    return templates.TemplateResponse(
        "profile.html", {"request": request, "user": user.model_dump()}
    )


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    delete_session_token_cookie(response)
    return response
