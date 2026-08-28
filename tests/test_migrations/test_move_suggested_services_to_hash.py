import json

from selfprivacy_api.migrations.move_suggested_services_to_hash import (
    MoveSuggestedServicesToHash,
)
from selfprivacy_api.services.suggested import SUGGESTED_SERVICES_REDIS_KEY
from selfprivacy_api.utils.redis_pool import RedisPool


async def test_migrates_legacy_suggested_service_keys(empty_redis_repo):
    redis = RedisPool().get_connection_async()
    definition = '{"meta": {"name": "Gitea"}}'
    await redis.set("suggestedservices:gitea:data", definition)
    await redis.set("suggestedservices:gitea:HEAD", "revision")
    migration = MoveSuggestedServicesToHash()

    assert await migration.is_migration_needed() is True
    await migration.migrate()

    assert json.loads(await redis.hget(SUGGESTED_SERVICES_REDIS_KEY, "gitea")) == {
        "revision": "revision",
        "definition": definition,
    }
    assert await redis.exists("suggestedservices:gitea:data") == 0
    assert await redis.exists("suggestedservices:gitea:HEAD") == 0
    assert await migration.is_migration_needed() is False
