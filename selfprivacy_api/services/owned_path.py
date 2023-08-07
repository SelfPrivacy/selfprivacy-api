from pydantic import BaseModel


class OwnedPath(BaseModel):
    path: str
    owner: str
    group: str
