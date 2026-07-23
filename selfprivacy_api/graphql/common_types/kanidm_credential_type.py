from typing import Optional

import strawberry

from selfprivacy_api.actions.kanidm_credential_type import (
    get_kanidm_minimum_credential_type as actions_get_kanidm_minimum_credential_type,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    MutationReturnInterface,
)
from selfprivacy_api.models.kanidm_credential_type import KanidmCredentialType


@strawberry.type
class KanidmCredentialTypeMutationReturn(MutationReturnInterface):
    """Return type for Kanidm Credential Type mutation"""

    minimum_credential_type: Optional[KanidmCredentialType] = None


async def get_minimum_kanidm_credential_type() -> KanidmCredentialType:
    """Get minimum kanidm credential type."""
    return await actions_get_kanidm_minimum_credential_type()
