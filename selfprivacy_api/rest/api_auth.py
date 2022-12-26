from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from selfprivacy_api.actions.api_tokens import (
    CannotDeleteCallerException,
    InvalidExpirationDate,
    InvalidUsesLeft,
    NotFoundException,
    delete_api_token,
    refresh_api_token,
    get_api_recovery_token_status,
    get_api_tokens_with_caller_flag,
    get_new_api_recovery_key,
    use_mnemonic_recovery_token,
    delete_new_device_auth_token,
    get_new_device_auth_token,
)

from selfprivacy_api.dependencies import TokenHeader, get_token_header

from selfprivacy_api.utils.auth import (
    use_new_device_auth_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.get("/tokens")
async def rest_get_tokens(auth_token: TokenHeader = Depends(get_token_header)):
    """Get the tokens info"""
    return get_api_tokens_with_caller_flag(auth_token.token)


class DeleteTokenInput(BaseModel):
    """Delete token input"""

    token_name: str


@router.delete("/tokens")
async def rest_delete_tokens(
    token: DeleteTokenInput, auth_token: TokenHeader = Depends(get_token_header)
):
    """Delete the tokens"""
    try:
        delete_api_token(auth_token.token, token.token_name)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Token not found")
    except CannotDeleteCallerException:
        raise HTTPException(status_code=400, detail="Cannot delete caller's token")
    return {"message": "Token deleted"}


@router.post("/tokens")
async def rest_refresh_token(auth_token: TokenHeader = Depends(get_token_header)):
    """Refresh the token"""
    try:
        new_token = refresh_api_token(auth_token.token)
    except NotFoundException:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"token": new_token}


@router.get("/recovery_token")
async def rest_get_recovery_token_status(
    auth_token: TokenHeader = Depends(get_token_header),
):
    return get_api_recovery_token_status()


class CreateRecoveryTokenInput(BaseModel):
    expiration: Optional[datetime] = None
    uses: Optional[int] = None


@router.post("/recovery_token")
async def rest_create_recovery_token(
    limits: CreateRecoveryTokenInput = CreateRecoveryTokenInput(),
    auth_token: TokenHeader = Depends(get_token_header),
):
    try:
        token = get_new_api_recovery_key(limits.expiration, limits.uses)
    except InvalidExpirationDate as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidUsesLeft as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"token": token}


class UseTokenInput(BaseModel):
    token: str
    device: str


@router.post("/recovery_token/use")
async def rest_use_recovery_token(input: UseTokenInput):
    token = use_mnemonic_recovery_token(input.token, input.device)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"token": token}


@router.post("/new_device")
async def rest_new_device(auth_token: TokenHeader = Depends(get_token_header)):
    token = get_new_device_auth_token()
    return {"token": token}


@router.delete("/new_device")
async def rest_delete_new_device_token(
    auth_token: TokenHeader = Depends(get_token_header),
):
    delete_new_device_auth_token()
    return {"token": None}


@router.post("/new_device/authorize")
async def rest_new_device_authorize(input: UseTokenInput):
    token = use_new_device_auth_token(input.token, input.device)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"message": "Device authorized", "token": token}
