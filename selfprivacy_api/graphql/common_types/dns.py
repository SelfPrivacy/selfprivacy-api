from typing import Optional
import strawberry


# TODO: use https://strawberry.rocks/docs/integrations/pydantic when it is stable
@strawberry.type
class DnsRecord:
    """DNS record"""

    record_type: str
    name: str
    content: str
    ttl: int
    priority: Optional[int]
    display_name: str
