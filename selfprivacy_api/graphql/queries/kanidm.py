"""Kanidm"""

# pylint: disable=too-few-public-methods
import strawberry

from selfprivacy_api.graphql import IsAuthenticated
from selfprivacy_api.graphql.common_types.kanidm_credential_type import (
    get_minimum_kanidm_credential_type as get_minimum_kanidm_credential_type_action,
)
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType


@strawberry.type
class Kanidm:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def minimum_credential_type(
        self,
    ) -> KanidmCredentialType:
        """Get minimum kanidm credential type"""

        return await get_minimum_kanidm_credential_type_action()
