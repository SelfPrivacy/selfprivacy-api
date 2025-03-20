from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, ValidationError
from selfprivacy_api.models.user import UserDataUser
from selfprivacy_api.userpanel.templates import templates
from selfprivacy_api.userpanel.auth.session import Session, delete_session_token_cookie
from selfprivacy_api.userpanel.routes.dependencies import get_current_user
from selfprivacy_api.services import ServiceManager
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    KanidmUserRepository,
)
from typing import Annotated

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class EditProfileForm(BaseModel):
    displayname: str = Field(..., min_length=1, max_length=255)


@router.get("/", response_class=HTMLResponse)
async def get_profile(
    request: Request, session: Annotated[Session, Depends(get_current_user)]
):
    try:
        user: UserDataUser = KanidmUserRepository.get_user_by_username(session.user_id)
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise HTTPException(status_code=500)
    enabled_services = ServiceManager.get_enabled_services_with_urls()
    # Prepare a list of services with their names, URLs, descriptions and icons.
    # If the service has an access group, check if the user is a member of that group
    # If not, do not include the service.
    # Split by @ and take the first part to get the group name
    if user.memberof is None:
        user_groups = []
    else:
        user_groups = [group.split("@")[0] for group in user.memberof]
    services = []
    for service in enabled_services:
        access_group = service.get_sso_access_group()
        if (access_group and (access_group in user_groups)) or not access_group:
            services.append(
                {
                    "name": service.get_display_name(),
                    "url": service.get_url(),
                    "description": service.get_description(),
                    "icon": service.get_svg_icon(raw=True),
                }
            )
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user.model_dump(), "services": services},
    )


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    delete_session_token_cookie(response)
    return response


@router.get("/edit", response_class=HTMLResponse)
async def edit_profile_get(
    request: Request, session: Annotated[Session, Depends(get_current_user)]
):
    try:
        user: UserDataUser = KanidmUserRepository.get_user_by_username(session.user_id)
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise HTTPException(status_code=500)
    return templates.TemplateResponse(
        "edit_profile.html",
        {"request": request, "values": {"displayname": user.displayname}, "errors": {}},
    )


@router.post("/edit", response_class=HTMLResponse)
async def edit_profile_post(
    request: Request,
    session: Annotated[Session, Depends(get_current_user)],
    displayname: Annotated[str, Form()],
):
    try:
        form = EditProfileForm(displayname=displayname)
    except ValidationError as e:
        errors = {err["loc"][0]: err["msg"] for err in e.errors()}
        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "values": {"displayname": displayname},
                "errors": errors,
            },
        )

    try:
        KanidmUserRepository.update_user(
            username=session.user_id, displayname=form.displayname
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500)

    return RedirectResponse(url="/user", status_code=303)
