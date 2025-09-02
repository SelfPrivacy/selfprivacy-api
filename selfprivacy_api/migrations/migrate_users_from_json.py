from typing import Optional
import logging
from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.models.user import UserDataUserOrigin
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    SP_ADMIN_GROUPS,
    SP_DEFAULT_GROUPS,
    KanidmUserRepository,
)
from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.actions.email_passwords import add_email_password_hash

from selfprivacy_api.utils import ReadUserData

logger = logging.getLogger(__name__)


class MigrateUsersFromJson(Migration):
    """Migrate users to kanidm, passwords to redis"""

    def _get_password_hash(self, username: str) -> Optional[str]:
        with ReadUserData() as data:
            if username == data.get("username"):
                return data.get("hashedMasterPassword")

            for user in data.get("users", []):
                if user.get("username") == username:
                    return user.get("hashedPassword", None)

    def _get_users_to_migrate(self):
        json_repo_users = JsonUserRepository.get_users(exclude_root=True)
        kanidm_repo_users = KanidmUserRepository.get_users(exclude_root=True)

        logger.info(
            f"Users in json repo: {[user.username for user in json_repo_users]}"
        )
        logger.info(
            f"Users in kanidm repo: {[user.username for user in kanidm_repo_users]}"
        )
        # Find the users from the json repo that are not in the kanidm repo
        # Search by username
        users_to_migrate = [
            user
            for user in json_repo_users
            if user.username
            not in [kanidm_user.username for kanidm_user in kanidm_repo_users]
        ]
        logger.info(f"Users to migrate: {users_to_migrate}")

        return users_to_migrate

    def get_migration_name(self) -> str:
        return "migrate_users_from_json"

    def get_migration_description(self) -> str:
        return "Migrate users to kanidm, passwords to redis."

    def is_migration_needed(self) -> bool:
        if self._get_users_to_migrate():
            return True
        return False

    def migrate(self) -> None:
        users_to_migrate = self._get_users_to_migrate()

        for user in users_to_migrate:
            password_hash = self._get_password_hash(username=user.username)

            try:
                if user.user_type == UserDataUserOrigin.PRIMARY:
                    KanidmUserRepository.create_user(
                        username=user.username,
                        directmemberof=SP_ADMIN_GROUPS,
                    )

                else:
                    KanidmUserRepository.create_user(
                        username=user.username, directmemberof=SP_DEFAULT_GROUPS
                    )

                if password_hash:
                    add_email_password_hash(
                        username=user.username,
                        password_hash=password_hash,
                        with_zero_uuid=True,
                    )
            except Exception as error:
                logger.error(f"Failed to migrate {user.username}. Error: {str(error)}")
