import asyncio
import pytest
from hashlib import sha256
from datetime import datetime, timedelta, timezone

import redis
from selfprivacy_api.utils.redis_pool import RedisPool

from selfprivacy_api.userpanel.auth.session import (
    create_session,
    validate_session_token,
    invalidate_session,
    Session,
)


def test_create_and_validate_session():
    token = "b6d3f8f2a7c44b7c8eac9f981f23d8c0"
    session: Session = asyncio.run(create_session(token=token, user_id="007"))

    session_id = sha256(token.encode()).hexdigest()

    expected = datetime.now(timezone.utc) + timedelta(hours=1)
    tolerance = timedelta(minutes=10)

    assert session.id == session_id
    assert session.user_id == "007"
    assert (session.expires_at - expected) <= tolerance

    assert validate_session_token(token) == session


def test_validate_non_exist_session():
    assert validate_session_token("09876543221") is None


def test_invalidate_session():
    token = "b6d3f8f2a7c44b7c8eac9f981f23d8c0"
    asyncio.run(create_session(token=token, user_id="007"))

    session_id = sha256(token.encode()).hexdigest()

    asyncio.run(invalidate_session(session_id))
