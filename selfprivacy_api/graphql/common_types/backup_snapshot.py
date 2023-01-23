import datetime
import strawberry


@strawberry.type
class SnapshotInfo:
    id: str
    service_name: str
    created_at: datetime.datetime
