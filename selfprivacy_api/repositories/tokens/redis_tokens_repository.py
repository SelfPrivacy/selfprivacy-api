"""
Token repository using Redis as backend.
"""
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)


class RedisTokensRepository(AbstractTokensRepository):
    """
    Token repository using Redis as a backend
    """

    def __init__(self) -> None:
        raise NotImplementedError
