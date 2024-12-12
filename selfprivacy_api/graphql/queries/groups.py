"""Groups"""

# pylint: disable=too-few-public-methods
import typing
import strawberry

from selfprivacy_api.graphql.common_types.groups import (
    Group,
    get_groups,
)
from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.actions.users import get_groups as action_get_groups


@strawberry.type
class Groups:
    all_groups: typing.List[Group] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_groups
    )

    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_groups() -> list:
        return action_get_groups()
