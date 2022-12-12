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
    RecoveryKeyNotFound,
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

    def create_token(self, device_name: str) -> Token:
        """Create new token"""
        new_token = Token.generate(device_name)

        self.__store_token(new_token)

        return new_token

    def __store_token(self, new_token: Token):
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

    def refresh_token(self, input_token: Token) -> Token:
        """Change the token field of the existing token"""
        new_token = Token.generate(device_name=input_token.device_name)

        with WriteUserData(UserDataFiles.TOKENS) as tokens_file:
            for userdata_token in tokens_file["tokens"]:

                if userdata_token["name"] == input_token.device_name:
                    userdata_token["token"] = new_token.token
                    userdata_token["date"] = (
                        new_token.created_at.strftime(DATETIME_FORMAT),
                    )

                    return new_token

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

    def use_mnemonic_recovery_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic recovery key and create a new token with the given name"""
        recovery_key = self.get_recovery_key()

        if recovery_key is None:
            raise RecoveryKeyNotFound("Recovery key not found")

        if not recovery_key.is_valid():
            raise RecoveryKeyNotFound("Recovery key not found")

        recovery_token = bytes.fromhex(recovery_key.key)

        if not Mnemonic(language="english").check(mnemonic_phrase):
            raise InvalidMnemonic("Phrase is not mnemonic!")

        phrase_bytes = Mnemonic(language="english").to_entropy(mnemonic_phrase)
        if phrase_bytes != recovery_token:
            raise RecoveryKeyNotFound("Recovery key not found")

        new_token = Token.generate(device_name=device_name)

        with WriteUserData(UserDataFiles.TOKENS) as tokens:
            tokens["tokens"].append(
                {
                    "token": new_token.token,
                    "name": new_token.device_name,
                    "date": new_token.created_at.strftime(DATETIME_FORMAT),
                }
            )

            if "recovery_token" in tokens:
                if (
                    "uses_left" in tokens["recovery_token"]
                    and tokens["recovery_token"]["uses_left"] is not None
                ):
                    tokens["recovery_token"]["uses_left"] -= 1
        return new_token

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

    def use_mnemonic_new_device_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic new device key"""

        with ReadUserData(UserDataFiles.TOKENS) as tokens_file:
            if "new_device" not in tokens_file or tokens_file["new_device"] is None:
                raise NewDeviceKeyNotFound("New device key not found")

            new_device_key = NewDeviceKey(
                key=tokens_file["new_device"]["token"],
                created_at=tokens_file["new_device"]["date"],
                expires_at=tokens_file["new_device"]["expiration"],
            )

        token = bytes.fromhex(new_device_key.key)

        if not Mnemonic(language="english").check(mnemonic_phrase):
            raise InvalidMnemonic("Phrase is not mnemonic!")

        phrase_bytes = Mnemonic(language="english").to_entropy(mnemonic_phrase)
        if bytes(phrase_bytes) != bytes(token):
            raise NewDeviceKeyNotFound("Phrase is not token!")

        new_token = Token.generate(device_name=device_name)
        with WriteUserData(UserDataFiles.TOKENS) as tokens:
            if "new_device" in tokens:
                del tokens["new_device"]

        return new_token
