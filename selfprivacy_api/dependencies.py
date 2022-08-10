from fastapi import Depends, FastAPI, HTTPException, status
from typing import Optional
from strawberry.fastapi import BaseContext
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from selfprivacy_api.utils.auth import is_token_valid


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


class GraphQlContext(BaseContext):
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token
        self.is_authenticated = auth_token is not None


async def get_graphql_context(
    token: str = Depends(
        APIKeyHeader(
            name="Authorization",
            auto_error=False,
        )
    )
) -> GraphQlContext:
    if token is None:
        return GraphQlContext()
    else:
        token = token.replace("Bearer ", "")
        if not is_token_valid(token):
            return GraphQlContext()
        return GraphQlContext(auth_token=token)


def get_api_version() -> str:
    """Get API version"""
    return "2.0.0"
