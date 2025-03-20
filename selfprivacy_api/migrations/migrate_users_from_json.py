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

        logger.info(f"Users in json repo: {json_repo_users}")
        logger.info(f"Users in kanidm repo: {kanidm_repo_users}")
        # Find the users from the json repo that are not in the kanidm repo
        # Search by username
        users_to_migrate = [user for user in json_repo_users if user.username not in [kanidm_user.username for kanidm_user in kanidm_repo_users]]
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
                        directmemberof=SP_ADMIN_GROUPS,  # TODO
                    )

                # [ 635µs | 22.47% / 100.00% ] method: POST | uri: /v1/person | version: HTTP/1.1
                # handle_create [ 493µs | 43.81% / 77.53% ]
                # ┝━ validate_client_auth_info_to_ident [ 214µs | 33.72% ]
                # │  ┕━ ｉ [info]: A valid session value exists for this token | event_tag_id: 10
                # ┝━ ｉ [info]: create initiator | event_tag_id: 10 | name: User( selfprivacy@bloodwine.cyou, bfe7c16a-5654-4c01-ad23-9e6b68901410 ) (e7bb32d6-03fd-409d-94ae-72aba8951bed, read write)
                # ┝━ ｉ [info]: entry matches acs | event_tag_id: 11 | entry_name: aadin | acs: "idm_acp_people_create"
                # ┝━ 🚨 [error]: create_attrs is not a subset of allowed | event_tag_id: 12
                # ┝━ 🚨 [error]: create: {"class", "directmemberof", "displayname", "mail", "name"} !⊆ allowed: {"account_expire", "account_valid_from", "class", "displayname", "mail", "name", "uuid"} | event_tag_id: 12
                # ┕━ ｉ [info]: denied ❌ - create may not proceed | event_tag_id: 11
                # 🚧 [warn]:  | latency: 661.49µs | status_code: 403 | kopid: "43800134-7c79-4cd5-9d10-d8929455d82f" | msg: "client error"

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
                logging.error(f"Failed to migrate {user.username}. Error: {str(error)}")
