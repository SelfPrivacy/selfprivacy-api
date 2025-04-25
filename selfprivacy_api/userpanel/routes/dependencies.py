from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from selfprivacy_api.userpanel.auth.session import (
    Session,
    validate_session_token,
    set_session_token_cookie,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(request: Request, response: Response) -> Session:
    """
    Retrieve the current user session based on the session token in the request cookies.

    Args:
        request (Request): The request object containing cookies.
        response (Response): The response object to set the session token cookie.

    Returns:
        Session: The user session if a valid session token is found.

    Raises:
        HTTPException: If no session token is found or if the session token is invalid.
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=303, headers={"Location": "/login"})

    session = await validate_session_token(session_token)
    if session is None:
        raise HTTPException(status_code=303, headers={"Location": "/user/logout"})
    else:
        set_session_token_cookie(response, session_token, session.expires_at)
        return session
