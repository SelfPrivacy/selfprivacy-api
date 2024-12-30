from typing import Optional

from pydantic import BaseModel


class Group(BaseModel):
    """
    Attributes:

    name (str): The name of the group.

    group_class (Optional[list[str]]):
        A list of group classes. This can be used to classify the
        group or assign it different roles/categories. Defaults to an empty list.

    member (Optional[list[str]]):
        A list of the groups within a given group.
        Optional, defaults to an empty list.

    memberof (Optional[list[str]]):
        A list of groups that this group is a member of.
        Optional, defaults to an empty list.

    directmemberof (Optional[list[str]]):
        A list of groups that directly contain this group as a member.
        Optional, defaults to an empty list.

    spn (Optional[str]):
        The Service Principal Name (SPN) associated with the group.
        Optional, defaults to None.

    description (Optional[str]):
        A textual description of the group. Optional, defaults to None.
    """

    name: str
    group_class: Optional[list[str]] = []
    member: Optional[list[str]] = []
    memberof: Optional[list[str]] = []
    directmemberof: Optional[list[str]] = []
    spn: Optional[str] = None
    description: Optional[str] = None
