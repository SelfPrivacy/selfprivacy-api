from typing import Optional

import strawberry

from selfprivacy_api.actions.users import get_groups as actions_get_groups


@strawberry.type
class Group:
    name: str
    group_class: Optional[list[str]] = strawberry.field(default_factory=list)
    member: Optional[list[str]] = strawberry.field(default_factory=list)
    memberof: Optional[list[str]] = strawberry.field(default_factory=list)
    directmemberof: Optional[list[str]] = strawberry.field(default_factory=list)
    spn: Optional[str] = None
    description: Optional[str] = None


def get_groups() -> list[Group]:
    """Get groups"""
    groups = actions_get_groups()
    return [
        Group(
            name=group.name,
            group_class=getattr(group, "group_class", []),
            member=getattr(group, "member", []),
            memberof=getattr(group, "memberof", []),
            directmemberof=getattr(group, "directmemberof", []),
            spn=getattr(group, "spn", None),
            description=getattr(group, "description", None),
        )
        for group in groups
    ]
