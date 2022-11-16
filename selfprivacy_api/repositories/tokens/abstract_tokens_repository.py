from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey


class AbstractTokensRepository(ABC):
    @abstractmethod
    def get_token_by_token_string(self, token_string: str) -> Optional[Token]:
        """Get the token by token"""

    @abstractmethod
    def get_token_by_name(self, token_name: str) -> Optional[Token]:
        """Get the token by name"""

    @abstractmethod
    def get_tokens(self) -> list[Token]:
        """Get the tokens"""

    @abstractmethod
    def create_token(self, device_name: str) -> Token:
        """Create new token"""

    @abstractmethod
    def delete_token(self, input_token: Token) -> None:
        """Delete the token"""

    @abstractmethod
    def refresh_token(self, input_token: Token) -> Token:
        """Refresh the token"""

    def is_token_valid(self, token_string: str) -> bool:
        """Check if the token is valid"""
        token = self.get_token_by_token_string(token_string)
        if token is None:
            return False
        return True

    def is_token_name_exists(self, token_name: str) -> bool:
        """Check if the token name exists"""
        token = self.get_token_by_name(token_name)
        if token is None:
            return False
        return True

    def is_token_name_pair_valid(self, token_name: str, token_string: str) -> bool:
        """Check if the token name and token are valid"""
        token = self.get_token_by_name(token_name)
        if token is None:
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

    @abstractmethod
    def use_mnemonic_recovery_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic recovery key and create a new token with the given name"""

    def is_recovery_key_valid(self) -> bool:
        """Check if the recovery key is valid"""
        recovery_key = self.get_recovery_key()
        if recovery_key is None:
            return False
        return recovery_key.is_valid()

    @abstractmethod
    def get_new_device_key(self) -> NewDeviceKey:
        """Creates and returns the new device key"""

    @abstractmethod
    def delete_new_device_key(self) -> None:
        """Delete the new device key"""

    @abstractmethod
    def use_mnemonic_new_device_key(
        self, mnemonic_phrase: str, device_name: str
    ) -> Token:
        """Use the mnemonic new device key"""
