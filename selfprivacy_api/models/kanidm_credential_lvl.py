from enum import Enum


class KanidmCredentialLvl(Enum):
    ANY = "ANY"  # no minimum (password-only allowed)
    MFA = "MFA"  # must be multi-factor (e.g., password + TOTP or passkey)
    PASSKEY = "PASSKEY"  # requires a WebAuthn passkey
