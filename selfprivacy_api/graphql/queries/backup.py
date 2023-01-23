"""Backup"""
# pylint: disable=too-few-public-methods
import typing
import strawberry
from selfprivacy_api.graphql.common_types.backup_snapshot import SnapshotInfo


@strawberry.type
class Backup:
    backend: str

    @strawberry.field
    def get_backups(self) -> typing.List[SnapshotInfo]:
        return []
