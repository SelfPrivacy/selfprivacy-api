import typing
import strawberry


@strawberry.type
class DnsRecord:
    """DNS record"""

    record_type: str
    name: str
    content: str
    ttl: int
    priority: typing.Optional[int]
    display_name: str
