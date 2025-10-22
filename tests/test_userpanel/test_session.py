import pytest

import asyncio
from hashlib import sha256
from datetime import datetime, timedelta, timezone

from selfprivacy_api.userpanel.auth.session import (
    create_session,
    validate_session_token,
    invalidate_session,
    generate_session_token,
    Session,
)


def _create_test_session():
    token = generate_session_token()
    assert token is not None

    session: Session = asyncio.run(create_session(token=token, user_id="007"))

    session_id = sha256(token.encode()).hexdigest()

    return session, session_id, token


def test_create_and_validate_session():
    session, session_id, token = _create_test_session()

    expected = datetime.now(timezone.utc) + timedelta(hours=1)
    tolerance = timedelta(minutes=10)

    assert session.id == session_id
    assert session.user_id == "007"
    assert (session.expires_at - expected) <= tolerance

    validated = asyncio.run(validate_session_token(token))

    assert validated is not None
    assert validated.id == session.id
    assert validated.user_id == session.user_id
    assert abs(validated.expires_at - session.expires_at) <= timedelta(seconds=10)


def test_validate_expired_session(monkeypatch):
    session, session_id, token = _create_test_session()

    datetime_now_plus2h = datetime.now(timezone.utc) + timedelta(hours=2)

    class PatchedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return (
                datetime_now_plus2h
                if tz is None
                else datetime_now_plus2h.astimezone(tz)
            )

    monkeypatch.setattr(
        "selfprivacy_api.userpanel.auth.session.datetime",
        PatchedDateTime,
        raising=True,
    )

    assert asyncio.run(validate_session_token(token)) is None


def test_validate_non_exist_session():
    assert asyncio.run(validate_session_token("40440404040404")) is None


def test_invalidate_session():
    session, session_id, token = _create_test_session()

    asyncio.run(invalidate_session(session_id))

    assert asyncio.run(validate_session_token(token)) is None
