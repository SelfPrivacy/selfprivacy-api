# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

from selfprivacy_api.migrations.write_token_to_redis import WriteTokenToRedis
from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)

from tests.test_migrations.conftest import set_api_secret


async def test_migrates_token_from_secrets(generic_userdata, empty_redis_repo):
    set_api_secret("token", "SECRET_TOKEN")
    migration = WriteTokenToRedis()

    assert await migration.is_migration_needed() is True

    await migration.migrate()

    tokens = await RedisTokensRepository().get_tokens()
    assert len(tokens) == 1
    assert tokens[0].token == "SECRET_TOKEN"
    assert tokens[0].device_name == "Initial device"
    assert await migration.is_migration_needed() is False


async def test_not_needed_when_redis_has_tokens(
    generic_userdata, redis_repo_with_tokens
):
    set_api_secret("token", "SECRET_TOKEN")

    assert await WriteTokenToRedis().is_migration_needed() is False


async def test_not_needed_without_token_in_secrets(generic_userdata, empty_redis_repo):
    # secrets.json is {} — the swallowed-KeyError path in get_token_from_json
    assert await WriteTokenToRedis().is_migration_needed() is False
    assert await RedisTokensRepository().get_tokens() == []
