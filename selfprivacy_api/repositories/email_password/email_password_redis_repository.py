from selfprivacy_api.models.email_password_metadata import EmailPasswordMetadata
from selfprivacy_api.repositories.email_password.abstract_email_password_repository import (
    AbstractEmailPasswordManager,
)
from selfprivacy_api.utils.redis_pool import RedisPool


redis = RedisPool().get_connection()


class EmailPasswordManager(AbstractEmailPasswordManager):
    @staticmethod
    def get_all_email_passwords_metadata(username: str) -> list[EmailPasswordMetadata]:
        pattern = f"priv/user/{username}/passwords/*"

        email_passwords_metadata = []
        cursor = 0

        while True:
            cursor, keys = redis.scan(cursor, match=pattern, count=100)  # type: ignore
            for key in keys:
                data = redis.hgetall(key)

                if data:
                    email_passwords_metadata.append(
                        EmailPasswordMetadata(
                            uuid=key.split("/")[-1],
                            display_name=data.get("display_name", None),  # type: ignore
                            created_at=data.get("created_at", None),  # type: ignore
                            expires_at=data.get("expires_at", None),  # type: ignore
                            last_used=data.get("last_used", None),  # type: ignore
                        )
                    )
            if (
                cursor == 0
            ):  # When SCAN finishes enumerating, it will retvurn cursor = 0
                break

        return email_passwords_metadata

    @staticmethod
    def add_new_email_password(
        username: str, password_hash: str, credential_metadata: EmailPasswordMetadata
    ) -> None:
        key = f"priv/user/{username}/passwords/{credential_metadata.uuid}"

        password_data = {
            "password_hash": password_hash,
            "display_name": credential_metadata.display_name,
            "created_at": credential_metadata.created_at,
        }

        redis.hmset(key, password_data)

    @staticmethod
    def delete_email_password(username: str, uuid: str) -> None:
        key = f"priv/user/{username}/passwords/{uuid}"

        redis.delete(key)

    @staticmethod
    def delete_all_email_passwords(username: str) -> None:
        pattern = f"priv/user/{username}/passwords/*"

        keys = redis.keys(pattern)

        if keys:
            redis.delete(*keys)
