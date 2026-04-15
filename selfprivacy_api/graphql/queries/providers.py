"""Enums representing different service providers."""

from enum import Enum

import strawberry


@strawberry.enum
class DnsProvider(Enum):
    CLOUDFLARE = "CLOUDFLARE"
    DIGITALOCEAN = "DIGITALOCEAN"
    DESEC = "DESEC"


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
