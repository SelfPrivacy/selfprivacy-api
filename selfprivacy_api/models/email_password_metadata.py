from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class EmailPasswordData(BaseModel):
    uuid: str
    hash: Optional[str] = None
    display_name: str
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
