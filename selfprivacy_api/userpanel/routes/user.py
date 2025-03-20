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
from selfprivacy_api.utils import get_domain
from selfprivacy_api.utils.icons import sanitize_svg
from selfprivacy_api.repositories.email_password import ACTIVE_EMAIL_PASSWORD_PROVIDER
from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from uuid import UUID

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
    if user.memberof is None:
        user_groups = []
    else:
        user_groups = [group.split("@")[0] for group in user.memberof]
    services = []
    for service in enabled_services:
        if service.get_id() == "selfprivacy-api":
            continue
        access_group = service.get_sso_access_group()
        if (access_group and (access_group in user_groups)) or not access_group:
            services.append(
                {
                    "name": service.get_display_name(),
                    "url": service.get_url(),
                    "description": service.get_description(),
                    "icon": sanitize_svg(service.get_svg_icon(raw=True)),
                }
            )

    kanidm_url = f"https://auth.{get_domain()}/ui/profile"

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user.model_dump(),
            "services": services,
            "kanidm_url": kanidm_url,
        },
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


@router.get("/email-passwords", response_class=HTMLResponse)
async def email_passwords_get(
    request: Request, session: Annotated[Session, Depends(get_current_user)]
):
    try:
        email_passwords: list[EmailPasswordData] = (
            ACTIVE_EMAIL_PASSWORD_PROVIDER.get_all_email_passwords_metadata(
                session.user_id
            )
        )

        email_passwords_dict = [
            email_password.model_dump() for email_password in email_passwords
        ]
        return templates.TemplateResponse(
            "email_passwords.html",
            {"request": request, "email_passwords": email_passwords_dict},
        )
    except Exception as e:
        logger.error(f"Error getting email passwords: {e}")
        raise HTTPException(status_code=500)


@router.post("/email-passwords/delete", response_class=HTMLResponse)
async def email_passwords_delete(
    request: Request,
    session: Annotated[Session, Depends(get_current_user)],
    uuid: Annotated[str, Form()],
):
    try:
        # Make sure the UUID is actually a valid UUID
        uuid = str(UUID(uuid))

        ACTIVE_EMAIL_PASSWORD_PROVIDER.delete_email_password_hash(
            session.user_id,
            uuid,
        )

        return RedirectResponse(url="/user/email-passwords", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting email password: {e}")
        raise HTTPException(status_code=400)
