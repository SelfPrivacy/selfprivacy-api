"""
temporary legacy
"""
from typing import Optional
from datetime import datetime, timezone

from selfprivacy_api.utils import UserDataFiles, WriteUserData, ReadUserData
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
)
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class JsonTokensRepository(AbstractTokensRepository):
    def get_tokens(self) -> list[Token]:
        """Get the tokens"""
        tokens_list = []

        with ReadUserData(UserDataFiles.TOKENS) as tokens_file:
            for userdata_token in tokens_file["tokens"]:
                tokens_list.append(
                    Token(
                        token=userdata_token["token"],
                        device_name=userdata_token["name"],
                        created_at=userdata_token["date"],
                    )
                )

        return tokens_list

    def _store_token(self, new_token: Token):
        """Store a token directly"""
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            tokens_file["tokens"].append(
                {
                    "token": new_token.token,
                    "name": new_token.device_name,
                    "date": new_token.created_at.strftime(DATETIME_FORMAT),
                }
            )

    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            for userdata_token in tokens_file["tokens"]:
                if userdata_token["token"] == input_token.token:
                    tokens_file["tokens"].remove(userdata_token)
                    return

        raise TokenNotFound("Token not found!")

    def __key_date_from_str(self, date_string: str) -> datetime:
        if date_string is None or date_string == "":
            return None
        # we assume that we store dates in json as naive utc
        utc_no_tz = datetime.fromisoformat(date_string)
        utc_with_tz = utc_no_tz.replace(tzinfo=timezone.utc)
        return utc_with_tz

    def __date_from_tokens_file(
        self, tokens_file: object, tokenfield: str, datefield: str
    ):
        date_string = tokens_file[tokenfield].get(datefield)
        return self.__key_date_from_str(date_string)

    def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""
        with ReadUserData(UserDataFiles.TOKENS) as tokens_file:

            if (
                "recovery_token" not in tokens_file
                or tokens_file["recovery_token"] is None
            ):
                return

            recovery_key = RecoveryKey(
                key=tokens_file["recovery_token"].get("token"),
                created_at=self.__date_from_tokens_file(
                    tokens_file, "recovery_token", "date"
                ),
                expires_at=self.__date_from_tokens_file(
                    tokens_file, "recovery_token", "expiration"
                ),
                uses_left=tokens_file["recovery_token"].get("uses_left"),
            )

            return recovery_key

    def create_recovery_key(
        self,
        expiration: Optional[datetime],
        uses_left: Optional[int],
    ) -> RecoveryKey:
        """Create the recovery key"""

        recovery_key = RecoveryKey.generate(expiration, uses_left)

        self._store_recovery_key(recovery_key)

        return recovery_key

    def _store_recovery_key(self, recovery_key: RecoveryKey) -> None:
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            key_expiration: Optional[str] = None
            if recovery_key.expires_at is not None:
                key_expiration = recovery_key.expires_at.strftime(DATETIME_FORMAT)
            tokens_file["recovery_token"] = {
                "token": recovery_key.key,
                "date": recovery_key.created_at.strftime(DATETIME_FORMAT),
                "expiration": key_expiration,
                "uses_left": recovery_key.uses_left,
            }

    def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""
        if self.is_recovery_key_valid():
            with WriteUserData(UserDataFiles.TOKENS) as tokens:
                if tokens["recovery_token"]["uses_left"] is not None:
                    tokens["recovery_token"]["uses_left"] -= 1

    def _delete_recovery_key(self) -> None:
        """Delete the recovery key"""
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            if "recovery_token" in tokens_file:
                del tokens_file["recovery_token"]
                return

    def _store_new_device_key(self, new_device_key: NewDeviceKey) -> None:
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            tokens_file["new_device"] = {
                "token": new_device_key.key,
                "date": new_device_key.created_at.strftime(DATETIME_FORMAT),
                "expiration": new_device_key.expires_at.strftime(DATETIME_FORMAT),
            }

    def delete_new_device_key(self) -> None:
        """Delete the new device key"""
        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            if "new_device" in tokens_file:
                del tokens_file["new_device"]
                return

    def _get_stored_new_device_key(self) -> Optional[NewDeviceKey]:
        """Retrieves new device key that is already stored."""
        with ReadUserData(UserDataFiles.TOKENS) as tokens_file:
            if "new_device" not in tokens_file or tokens_file["new_device"] is None:
                return

            new_device_key = NewDeviceKey(
                key=tokens_file["new_device"]["token"],
                created_at=tokens_file["new_device"]["date"],
                expires_at=tokens_file["new_device"]["expiration"],
            )
            return new_device_key
