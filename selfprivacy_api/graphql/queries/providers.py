"""Enums representing different service providers."""

from enum import Enum

import strawberry


@strawberry.enum
class DnsProvider(Enum):
    CLOUDFLARE = "CLOUDFLARE"
    DIGITALOCEAN = "DIGITALOCEAN"
    DESEC = "DESEC"
    PORKBUN = "PORKBUN"

    def needs_token_id(self) -> bool:
        return self in {DnsProvider.PORKBUN}

    def needs_url(self) -> bool:
        return False

    def needs_tenant(self) -> bool:
        return False

    def needs_secondary_token(self) -> bool:
        return False


@strawberry.enum
class ServerProvider(Enum):
    HETZNER = "HETZNER"
    DIGITALOCEAN = "DIGITALOCEAN"
    OTHER = "OTHER"


@strawberry.enum
class BackupProvider(Enum):
    BACKBLAZE = "BACKBLAZE"
    NONE = "NONE"
    # for testing purposes, make sure not selectable in prod.
    MEMORY = "MEMORY"
    FILE = "FILE"
