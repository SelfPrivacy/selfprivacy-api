"""
temporary legacy
"""
from typing import Optional
from datetime import datetime
from mnemonic import Mnemonic

from selfprivacy_api.utils import UserDataFiles, WriteUserData, ReadUserData
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
    InvalidMnemonic,
    NewDeviceKeyNotFound,
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
                created_at=tokens_file["recovery_token"].get("date"),
                expires_at=tokens_file["recovery_token"].get("expitation"),
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

        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            tokens_file["recovery_token"] = {
                "token": recovery_key.key,
                "date": recovery_key.created_at.strftime(DATETIME_FORMAT),
                "expiration": recovery_key.expires_at,
                "uses_left": recovery_key.uses_left,
            }

        return recovery_key

    def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""
        if self.is_recovery_key_valid():
            with WriteUserData(UserDataFiles.TOKENS) as tokens:
                tokens["recovery_token"]["uses_left"] -= 1

    def get_new_device_key(self) -> NewDeviceKey:
        """Creates and returns the new device key"""
        new_device_key = NewDeviceKey.generate()

        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            tokens_file["new_device"] = {
                "token": new_device_key.key,
                "date": new_device_key.created_at.strftime(DATETIME_FORMAT),
                "expiration": new_device_key.expires_at.strftime(DATETIME_FORMAT),
            }

        return new_device_key

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

    def use_mnemonic_new_device_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic new device key"""
        new_device_key = self._get_stored_new_device_key()
        if not new_device_key:
            raise NewDeviceKeyNotFound

        if not self._assert_mnemonic(new_device_key.key, mnemonic_phrase):
            raise NewDeviceKeyNotFound("Phrase is not token!")

        new_token = self.create_token(device_name=device_name)
        self.delete_new_device_key()

        return new_token
