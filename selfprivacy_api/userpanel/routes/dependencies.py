from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from selfprivacy_api.userpanel.auth.session import (
    Session,
    validate_session_token,
    set_session_token_cookie,
    delete_session_token_cookie,
)

import logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



async def get_current_user(
    request: Request, response: Response
) -> RedirectResponse | Session:
    session_token = request.cookies.get("session_token")
    if not session_token:
        logger.warning("No session token found, redirecting to login.")
        return RedirectResponse(url="/login")

    session = await validate_session_token(session_token)
    if session is None:
        logger.warning("Invalid session token, deleting cookie and redirecting to login.")
        delete_session_token_cookie(response)
        return RedirectResponse(url="/login")
    else:
        logger.info("Valid session token found, setting cookie.")
        set_session_token_cookie(response, session_token, session.expires_at)
        return session
