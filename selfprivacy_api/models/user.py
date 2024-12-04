from enum import Enum
from pydantic import BaseModel
from typing import Optional


class UserDataUserOrigin(Enum):
    """Origin of the user in the user data"""

    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


class UserDataUser(BaseModel):
    """The user model from the userdata file"""

    username: str

    ssh_keys: Optional[list[str]] = []
    user_type: Optional[UserDataUserOrigin] = None
    displayname: Optional[str] = (
        None  # in logic graphql will return "username" if "displayname" None
    )

    email: Optional[str] = None
    directmemberof: Optional[list[str]] = None
    memberof: Optional[list[str]] = None
