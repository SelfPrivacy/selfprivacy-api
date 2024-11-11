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
    displayname: Optional[str]
    ssh_keys: list[str]
    origin: UserDataUserOrigin
    email: Optional[str]
