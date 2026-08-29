from enum import Enum


class KanidmCredentialType(Enum):
    any = "any"  # no minimum (password-only allowed)
    mfa = "mfa"  # must be multi-factor (e.g., password + TOTP or passkey)
    passkey = "passkey"  # requires a WebAuthn passkey
    attested_passkey = "attested_passkey"  # requires a trusted WebAuthn passkey
