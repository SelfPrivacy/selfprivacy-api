"""Groups"""

# pylint: disable=too-few-public-methods
from typing import List

import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.groups import (
    Group,
    get_groups,
)


@strawberry.type
class Groups:
    all_groups: List[Group] = strawberry.field(
        permission_classes=[IsAuthenticated], resolver=get_groups
    )
