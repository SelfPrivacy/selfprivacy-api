from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from mnemonic import Mnemonic

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
    InvalidMnemonic,
    RecoveryKeyNotFound,
    NewDeviceKeyNotFound,
)
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey


class AbstractTokensRepository(ABC):
    def get_token_by_token_string(self, token_string: str) -> Optional[Token]:
        """Get the token by token"""
        tokens = self.get_tokens()
        for token in tokens:
            if token.token == token_string:
                return token

        raise TokenNotFound("Token not found!")

    def get_token_by_name(self, token_name: str) -> Optional[Token]:
        """Get the token by name"""
        tokens = self.get_tokens()
        for token in tokens:
            if token.device_name == token_name:
                return token

        raise TokenNotFound("Token not found!")

    @abstractmethod
    def get_tokens(self) -> list[Token]:
        """Get the tokens"""

    def create_token(self, device_name: str) -> Token:
        """Create new token"""
        new_token = Token.generate(device_name)

        self._store_token(new_token)

        return new_token

    @abstractmethod
    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""

    def refresh_token(self, input_token: Token) -> Token:
        """Change the token field of the existing token"""
        new_token = Token.generate(device_name=input_token.device_name)
        new_token.created_at = input_token.created_at

        if input_token in self.get_tokens():
            self.delete_token(input_token)
            self._store_token(new_token)
            return new_token

        raise TokenNotFound("Token not found!")

    def is_token_valid(self, token_string: str) -> bool:
        """Check if the token is valid"""
        token = self.get_token_by_token_string(token_string)
        if token is None:
            return False
        return True

    def is_token_name_exists(self, token_name: str) -> bool:
        """Check if the token name exists"""
        return token_name in [token.device_name for token in self.get_tokens()]

    def is_token_name_pair_valid(self, token_name: str, token_string: str) -> bool:
        """Check if the token name and token are valid"""
        try:
            token = self.get_token_by_name(token_name)
            if token is None:
                return False
        except TokenNotFound:
            return False
        return token.token == token_string

    @abstractmethod
    def get_recovery_key(self) -> Optional[RecoveryKey]:
        """Get the recovery key"""

    @abstractmethod
    def create_recovery_key(
        self,
        expiration: Optional[datetime],
        uses_left: Optional[int],
    ) -> RecoveryKey:
        """Create the recovery key"""

    def use_mnemonic_recovery_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic recovery key and create a new token with the given name"""
        if not self.is_recovery_key_valid():
            raise RecoveryKeyNotFound("Recovery key not found")

        recovery_hex_key = self.get_recovery_key().key
        if not self._assert_mnemonic(recovery_hex_key, mnemonic_phrase):
            raise RecoveryKeyNotFound("Recovery key not found")

        new_token = self.create_token(device_name=device_name)

        self._decrement_recovery_token()

        return new_token

    def is_recovery_key_valid(self) -> bool:
        """Check if the recovery key is valid"""
        recovery_key = self.get_recovery_key()
        if recovery_key is None:
            return False
        return recovery_key.is_valid()

    def get_new_device_key(self) -> NewDeviceKey:
        """Creates and returns the new device key"""
        new_device_key = NewDeviceKey.generate()
        self._store_new_device_key(new_device_key)

        return new_device_key

    def _store_new_device_key(self, new_device_key: NewDeviceKey) -> None:
        """Store new device key directly"""

    @abstractmethod
    def delete_new_device_key(self) -> None:
        """Delete the new device key"""

    def use_mnemonic_new_device_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic new device key"""
        new_device_key = self._get_stored_new_device_key()
        if not new_device_key:
            raise NewDeviceKeyNotFound

        if not new_device_key.is_valid():
            raise NewDeviceKeyNotFound

        if not self._assert_mnemonic(new_device_key.key, mnemonic_phrase):
            raise NewDeviceKeyNotFound("Phrase is not token!")

        new_token = self.create_token(device_name=device_name)
        self.delete_new_device_key()

        return new_token

    @abstractmethod
    def _store_token(self, new_token: Token):
        """Store a token directly"""

    @abstractmethod
    def _decrement_recovery_token(self):
        """Decrement recovery key use count by one"""

    @abstractmethod
    def _get_stored_new_device_key(self) -> Optional[NewDeviceKey]:
        """Retrieves new device key that is already stored."""

    # TODO: find a proper place for it
    def _assert_mnemonic(self, hex_key: str, mnemonic_phrase: str):
        """Return true if hex string matches the phrase, false otherwise
        Raise an InvalidMnemonic error if not mnemonic"""
        recovery_token = bytes.fromhex(hex_key)
        if not Mnemonic(language="english").check(mnemonic_phrase):
            raise InvalidMnemonic("Phrase is not mnemonic!")

        phrase_bytes = Mnemonic(language="english").to_entropy(mnemonic_phrase)
        return phrase_bytes == recovery_token
