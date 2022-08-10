"""Users management module"""
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

import selfprivacy_api.actions.users as users_actions

from selfprivacy_api.dependencies import get_token_header

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("")
async def get_users(withMainUser: bool = False):
    """Get the list of users"""
    users: list[users_actions.UserDataUser] = users_actions.get_users(
        exclude_primary=not withMainUser, exclude_root=True
    )

    return [user.username for user in users]


class UserInput(BaseModel):
    """User input"""

    username: str
    password: str


@router.post("", status_code=201)
async def create_user(user: UserInput):
    try:
        users_actions.create_user(user.username, user.password)
    except users_actions.PasswordIsEmpty as e:
        raise HTTPException(status_code=400, detail=str(e))
    except users_actions.UsernameForbidden as e:
        raise HTTPException(status_code=409, detail=str(e))
    except users_actions.UsernameNotAlphanumeric as e:
        raise HTTPException(status_code=400, detail=str(e))
    except users_actions.UsernameTooLong as e:
        raise HTTPException(status_code=400, detail=str(e))
    except users_actions.UserAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {"result": 0, "username": user.username}


@router.delete("/{username}")
async def delete_user(username: str):
    try:
        users_actions.delete_user(username)
    except users_actions.UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except users_actions.UserIsProtected as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"result": 0, "username": username}
