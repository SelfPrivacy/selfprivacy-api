"""Kanidm"""

# pylint: disable=too-few-public-methods
from typing import Optional

import strawberry

from selfprivacy_api.graphql.common_types.kanidm_credential_type import (
    get_minimum_kanidm_credential_type as get_minimum_kanidm_credential_type_action,
    KanidmCredentialType,
)
from selfprivacy_api.graphql import IsAuthenticated


@strawberry.type
class Kanidm:
    @strawberry.field(permission_classes=[IsAuthenticated])
    def get_minimum_kanidm_credential_type(self) -> Optional[KanidmCredentialType]:
        """Get minimum kanidm credential type"""

        return get_minimum_kanidm_credential_type_action()
