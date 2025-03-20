from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from selfprivacy_api.userpanel.auth.session import Session
from selfprivacy_api.userpanel.routes.dependencies import get_current_user
from typing import Annotated

router = APIRouter()
templates = Jinja2Templates(directory="selfprivacy_api/userpanel/templates")


@router.get("/")
async def get_profile(
    request: Request, user: Annotated[Session, Depends(get_current_user)]
):
    return templates.TemplateResponse(
        "profile.html", {"request": request, "username": user.user_id}
    )
