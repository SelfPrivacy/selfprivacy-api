from enum import Enum
from pydantic import BaseModel
from typing import Optional

from selfprivacy_api.models.email_password_metadata import EmailPasswordMetadata


class UserDataUserOrigin(Enum):
    """Origin of the user in the user data"""

    NORMAL = "NORMAL"
    PRIMARY = "PRIMARY"
    ROOT = "ROOT"


class UserDataUser(BaseModel):
    """The user model from the userdata file"""

    username: str
    user_type: UserDataUserOrigin
    ssh_keys: list[str] = []
    directmemberof: Optional[list[str]] = []
    memberof: Optional[list[str]] = []
    displayname: Optional[str] = (
        None  # in logic graphql will return "username" if "displayname" None
    )
    email: Optional[str] = None
    email_credentials_metadata: list[EmailPasswordMetadata] = []
