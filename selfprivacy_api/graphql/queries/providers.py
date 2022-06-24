"""Enums representing different service providers."""
from enum import Enum
import datetime
import typing
import strawberry


@strawberry.enum
class DnsProvider(Enum):
    CLOUDFLARE = "CLOUDFLARE"


@strawberry.enum
class ServerProvider(Enum):
    HETZNER = "HETZNER"
