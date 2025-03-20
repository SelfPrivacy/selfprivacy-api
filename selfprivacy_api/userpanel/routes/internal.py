from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from selfprivacy_api.utils.self_service_portal_utils import validate_email_password
from selfprivacy_api.utils import get_domain
from typing import Annotated

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/check-email-password")
async def check_email_password(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    headers = request.headers
    logger.info("Headers:")
    for key, value in headers.items():
        logger.info(f"{key}: {value}")

    if not username or not password:
        logger.error("Invalid request")
        return JSONResponse({"isValid": False}, status_code=400)

    if "@" in username:
        parsed_user, domain = username.split("@")
        if domain != get_domain():
            logger.error(f"Invalid domain for user: {username}")
            return JSONResponse({"isValid": False}, status_code=400)
        user = parsed_user
    else:
        logger.error("Invalid input: username must contain a domain")
        return JSONResponse({"isValid": False}, status_code=400)

    try:
        is_valid = validate_email_password(user, password)
        logger.info(
            f"Password for user {username} is {'valid' if is_valid else 'invalid'}"
        )
        return JSONResponse({"isValid": is_valid})
    except Exception as e:
        logger.error(f"Error validating user: {e}")
        return JSONResponse({"isValid": False}, status_code=400)
