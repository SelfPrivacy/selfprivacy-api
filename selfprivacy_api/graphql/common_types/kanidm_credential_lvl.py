from enum import Enum

import strawberry

from selfprivacy_api.actions.kanidm_credential_lvl import (
    get_kanidm_credential_lvl as actions_get_kanidm_credential_lvl,
)


@strawberry.enum
class KanidmCredentialLvlType(Enum):
    ANY = "ANY"  # no minimum (password-only allowed)
    MFA = "MFA"  # must be multi-factor (e.g., password + TOTP or passkey)
    PASSKEY = "PASSKEY"  # requires a WebAuthn passkey


@strawberry.type
class KanidmCredentialLvl:
    minimum_credential_lvl: KanidmCredentialLvlType


def get_kanidm_credential_lvl() -> KanidmCredentialLvl:
    """Get KanidmCredentialLvl"""
    minimum_credential_lvl = actions_get_kanidm_credential_lvl()

    enum_val = KanidmCredentialLvlType[minimum_credential_lvl.name]
    return KanidmCredentialLvl(minimum_credential_lvl=enum_val)  # type: ignore[call-arg]
