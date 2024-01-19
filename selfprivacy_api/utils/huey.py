"""MiniHuey singleton."""
import os
from os import environ
from huey import RedisHuey

from selfprivacy_api.utils.redis_pool import RedisPool

HUEY_DATABASE_NUMBER = 10

def immediate() -> bool:
    if environ.get("HUEY_QUEUES_FOR_TESTS"):
        return False
    if environ.get("TEST_MODE"):
        return True
    return False

# Singleton instance containing the huey database.
huey = RedisHuey(
    "selfprivacy-api",
    url=RedisPool.connection_url(dbnumber=HUEY_DATABASE_NUMBER),
    immediate=immediate(),
    utc=True,
)
