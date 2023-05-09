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


@strawberry.enum
class BackupProvider(Enum):
    BACKBLAZE = "BACKBLAZE"
