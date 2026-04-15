from typing import Optional

import strawberry

from selfprivacy_api.graphql.common_types.jobs import ApiJob


@strawberry.interface
class MutationReturnInterface:
    success: bool
    message: str
    code: int


@strawberry.type
class GenericMutationReturn(MutationReturnInterface):
    pass


@strawberry.type
class GenericJobMutationReturn(MutationReturnInterface):
    job: Optional[ApiJob] = None
