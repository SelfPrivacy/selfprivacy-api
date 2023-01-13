from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)


class LoadTokensToRedis(Migration):
    """Load Json tokens into Redis"""

    def get_migration_name(self):
        return "load_tokens_to_redis"

    def get_migration_description(self):
        return "Loads access tokens and recovery keys from legacy json file into redis token storage"

    def is_repo_empty(self, repo: AbstractTokensRepository) -> bool:
        if repo.get_tokens() != []:
            return False
        if repo.get_recovery_key() is not None:
            return False
        return True

    def is_migration_needed(self):
        try:
            if not self.is_repo_empty(JsonTokensRepository()) and self.is_repo_empty(
                RedisTokensRepository()
            ):
                return True
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Write info about providers to userdata.json
        try:
            RedisTokensRepository().clone(JsonTokensRepository())

            print("Done")
        except Exception as e:
            print(e)
            print("Error migrating access tokens from json to redis")
