from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from selfprivacy_api.actions.api_tokens import is_token_valid


class TokenHeader(BaseModel):
    token: str


async def get_token_header(
    token: str = Depends(APIKeyHeader(name="Authorization", auto_error=False))
) -> TokenHeader:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not provided"
        )
    else:
        token = token.replace("Bearer ", "")
        if not is_token_valid(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        return TokenHeader(token=token)


def get_api_version() -> str:
    """Get API version"""
    return "3.6.0"
