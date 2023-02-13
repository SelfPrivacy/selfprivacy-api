from pydantic import BaseModel

class Snapshot(BaseModel):
    id: str
    service_name: str
    created_at: datetime.datetime
