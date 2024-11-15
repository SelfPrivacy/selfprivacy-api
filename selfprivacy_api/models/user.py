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
    origin: UserDataUserOrigin

    displayname: Optional[
        str
    ]  # in logic graphql will return "username" if "displayname" None
    uuid: Optional[str]
    email: Optional[str]
    ssh_keys: Optional[list[str]]
    directmemberof: Optional[list[str]]
    memberof: Optional[list[str]]
