from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)
from selfprivacy_api.utils import ReadUserData, UserDataFiles


class WriteTokenToRedis(Migration):
    """Load Json tokens into Redis"""

    def get_migration_name(self):
        return "write_token_to_redis"

    def get_migration_description(self):
        return "Loads the initial token into redis token storage"

    def is_repo_empty(self, repo: AbstractTokensRepository) -> bool:
        if repo.get_tokens() != []:
            return False
        return True

    def get_token_from_json(self):
        try:
            with ReadUserData(UserDataFiles.SECRETS) as userdata:
                return userdata["api"]["token"]
        except Exception as e:
            print(e)
            return None

    def is_migration_needed(self):
        try:
            if self.get_token_from_json() is not None and self.is_repo_empty(
                RedisTokensRepository()
            ):
                return True
        except Exception as e:
            print(e)
            return False

    def migrate(self):
        # Write info about providers to userdata.json
        try:
            token = self.get_token_from_json()
            if token is None:
                print("No token found in tokens.json")
                return
            RedisTokensRepository()._store_token(token)

            print("Done")
        except Exception as e:
            print(e)
            print("Error migrating access tokens from json to redis")
