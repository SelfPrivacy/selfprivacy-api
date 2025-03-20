from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from selfprivacy_api.userpanel.auth.session import (
    Session,
    validate_session_token,
    set_session_token_cookie,
    delete_session_token_cookie,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    request: Request, response: Response
) -> RedirectResponse | Session:
    session_token = request.cookies.get("session_token")
    if not session_token:
        return RedirectResponse(url="/login")

    session = await validate_session_token(session_token)
    if session is None:
        delete_session_token_cookie(response)
        return RedirectResponse(url="/login")
    else:
        set_session_token_cookie(response, session_token, session.expires_at)
        return session
