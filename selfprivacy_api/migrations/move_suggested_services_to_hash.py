"""Move suggested-service metadata from per-service keys to one Redis hash."""

import json

from selfprivacy_api.migrations.migration import Migration
from selfprivacy_api.services.suggested import SUGGESTED_SERVICES_REDIS_KEY
from selfprivacy_api.utils.redis_pool import RedisPool


class MoveSuggestedServicesToHash(Migration):
    def get_migration_name(self) -> str:
        return "move_suggested_services_to_hash"

    def get_migration_description(self) -> str:
        return "Stores suggested service metadata in a single Redis hash"

    async def is_migration_needed(self) -> bool:
        redis = await RedisPool().get_connection_async()
        if await redis.exists(SUGGESTED_SERVICES_REDIS_KEY):
            return False
        async for _ in redis.scan_iter("suggestedservices:*:data"):
            return True
        return False

    async def migrate(self) -> None:
        redis = await RedisPool().get_connection_async()
        data_keys = [key async for key in redis.scan_iter("suggestedservices:*:data")]
        if not data_keys:
            return

        async with redis.pipeline(transaction=True) as pipe:
            for data_key in data_keys:
                service_id = data_key.removeprefix("suggestedservices:").removesuffix(
                    ":data"
                )
                pipe.get(data_key)
                pipe.get(f"suggestedservices:{service_id}:HEAD")
            results = await pipe.execute()

        async with redis.pipeline(transaction=True) as pipe:
            for data_key, (definition, revision) in zip(
                data_keys, zip(results[::2], results[1::2])
            ):
                if definition is None:
                    continue
                service_id = data_key.removeprefix("suggestedservices:").removesuffix(
                    ":data"
                )
                pipe.hset(
                    SUGGESTED_SERVICES_REDIS_KEY,
                    service_id,
                    json.dumps(
                        {
                            "revision": revision,
                            "definition": definition,
                        }
                    ),
                )
                pipe.delete(data_key, f"suggestedservices:{service_id}:HEAD")
            await pipe.execute()
