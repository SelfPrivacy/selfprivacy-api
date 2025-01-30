from selfprivacy_api.migrations.migration import Migration

from selfprivacy_api.models.user import UserDataUserOrigin
from selfprivacy_api.repositories.users.kanidm_user_repository import (
    ADMIN_GROUPS,
    KanidmUserRepository,
)
from selfprivacy_api.repositories.users.json_user_repository import JsonUserRepository

from selfprivacy_api.actions.users import create_user


class MigrateUsersToKanidm(Migration):
    """Migrate users to kanidm."""

    def __init__(self):
        self.users_to_migrate = None

    def get_migration_name(self) -> str:
        return "migrate_users_to_kanidm"

    def get_migration_description(self) -> str:
        return "Migrate users to kanidm."

    def is_migration_needed(self) -> bool:
        json_repo_users = JsonUserRepository.get_users(exclude_root=True)
        kanidm_repo_users = KanidmUserRepository.get_users(exclude_root=True)

        self.users_to_migrate = [
            user for user in json_repo_users if user not in kanidm_repo_users
        ]

        return bool(self.users_to_migrate)

    def migrate(self) -> None:
        for user in self.users_to_migrate:  # type: ignore

            if user.user_type == UserDataUserOrigin.PRIMARY:
                create_user(
                    username=user.username,
                    directmemberof=ADMIN_GROUPS,
                )

            create_user(username=user.username)
