from typing import Optional
from pydantic import BaseModel


class EmailPasswordMetadata(BaseModel):
    uuid: str
    display_name: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    last_used: Optional[str] = None
