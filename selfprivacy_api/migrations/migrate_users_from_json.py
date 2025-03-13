from typing import Optional
import logging
from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.models.user import UserDataUserOrigin
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    ADMIN_GROUPS,
    KanidmUserRepository,
)
from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository
from selfprivacy_api.actions.email_passwords import add_email_password

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

        return [user for user in json_repo_users if user not in kanidm_repo_users]

    def get_migration_name(self) -> str:
        return "migrate_users_from_json"

    def get_migration_description(self) -> str:
        return "Migrate users to kanidm, passwords to redis."

    def is_migration_needed(self) -> bool:
        if self._get_users_to_migrate:
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
                        directmemberof=ADMIN_GROUPS,
                    )
                else:
                    KanidmUserRepository.create_user(username=user.username)

                if password_hash:
                    add_email_password(
                        username=user.username,
                        password_hash=password_hash,
                    )
            except Exception as error:
                logging.error(f"Failed to migrate {user.username}. Error: {str(error)}")
