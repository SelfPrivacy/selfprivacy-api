from typing import Optional

from pydantic import BaseModel


class Group(BaseModel):
    name: str
    group_class: Optional[list[str]] = []
    member: Optional[list[str]] = []
    memberof: Optional[list[str]] = []
    directmemberof: Optional[list[str]] = []
    spn: Optional[str] = None
    description: Optional[str] = None
