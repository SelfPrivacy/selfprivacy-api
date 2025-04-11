import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from selfprivacy_api.utils.self_service_portal_utils import validate_email_password
from selfprivacy_api.utils import get_domain

logger = logging.getLogger(__name__)

router = APIRouter()


class EmailPasswordCheckInput(BaseModel):
    username: str
    password: str


@router.post("/check-email-password")
async def check_email_password(request: Request, input_data: EmailPasswordCheckInput):

    username = input_data.username
    password = input_data.password

    if not username or not password:
        return JSONResponse({"isValid": False}, status_code=400)

    if "@" in username:
        parsed_user, domain = username.rsplit("@", 1)
        if domain != get_domain():
            return JSONResponse({"isValid": False}, status_code=400)
        user = parsed_user
    else:
        return JSONResponse({"isValid": False}, status_code=400)

    try:
        is_valid = validate_email_password(user, password)
        return JSONResponse({"isValid": is_valid})
    except Exception as e:
        logger.error(f"Error validating user: {e}")
        return JSONResponse({"isValid": False}, status_code=400)
