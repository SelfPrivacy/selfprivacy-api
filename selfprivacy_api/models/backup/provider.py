from pydantic import BaseModel

"""for storage in Redis"""


class BackupProviderModel(BaseModel):
    kind: str
    login: str
    key: str
    location: str
    repo_id: str  # for app usage, not for us
