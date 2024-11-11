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

    uuid: Optional[str]
    displayname: Optional[str]
    email: Optional[str]

    username: str
    ssh_keys: list[str]  # TODO WHY NOT OPTIONAL?
    origin: UserDataUserOrigin
