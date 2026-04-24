from enum import Enum
from typing import Optional

import strawberry

from selfprivacy_api.actions.kanidm_credential_type import (
    get_kanidm_minimum_credential_type as actions_get_kanidm_minimum_credential_type,
)
from selfprivacy_api.graphql.mutations.mutation_interface import (
    MutationReturnInterface,
)


@strawberry.enum
class KanidmCredentialType(Enum):
    any = "any"  # no minimum (password-only allowed)
    mfa = "mfa"  # must be multi-factor (e.g., password + TOTP or passkey)
    passkey = "passkey"  # requires a WebAuthn passkey


@strawberry.type
class KanidmCredentialTypeMutationReturn(MutationReturnInterface):
    """Return type for Kanidm Credential Type mutation"""

    minimum_credential_type: Optional[KanidmCredentialType] = None


async def get_minimum_kanidm_credential_type() -> KanidmCredentialType:
    """Get minimum kanidm credential type."""
    minimum_credential_type = await actions_get_kanidm_minimum_credential_type()

    return KanidmCredentialType[minimum_credential_type.name]
