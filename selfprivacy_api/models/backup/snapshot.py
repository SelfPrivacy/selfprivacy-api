import datetime
from pydantic import BaseModel

from selfprivacy_api.graphql.common_types.backup import BackupReason


class Snapshot(BaseModel):
    id: str
    service_name: str
    created_at: datetime.datetime
    reason: BackupReason
