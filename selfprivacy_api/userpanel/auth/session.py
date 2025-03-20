from fastapi import Response
from selfprivacy_api.utils.redis_pool import RedisPool
import secrets
import base64
from hashlib import sha256
from datetime import datetime, timedelta
import json


def generate_password() -> str:
    return secrets.token_urlsafe(32)


def generate_session_token() -> str:
    bytes = secrets.token_bytes(32)
    token = base64.b32encode(bytes).decode("utf-8").rstrip("=").lower()
    return token


class Session:
    def __init__(self, id: str, user_id: str, expires_at: datetime):
        self.id = id
        self.user_id = user_id
        self.expires_at = expires_at


async def create_session(token: str, user_id: str) -> Session:
    redis_conn = RedisPool().get_userpanel_connection_async()

    if redis_conn is None:
        raise Exception("Redis storage is not available")

    session_id = sha256(token.encode()).hexdigest()
    expires_at = datetime.now() + timedelta(hours=1)
    session = Session(id=session_id, user_id=user_id, expires_at=expires_at)

    session_data = {
        "id": session.id,
        "user_id": session.user_id,
        "expires_at": int(session.expires_at.timestamp()),
    }

    await redis_conn.set(
        f"session:{session_id}",
        json.dumps(session_data),
        exat=int(session.expires_at.timestamp()),
    )

    return session


async def validate_session_token(token: str) -> Session | None:
    redis_conn = RedisPool().get_userpanel_connection_async()

    session_id = sha256(token.encode()).hexdigest()
    item = await redis_conn.get(f"session:{session_id}")
    if item is None:
        return None

    result = json.loads(item)
    session = Session(
        id=result["id"],
        user_id=result["user_id"],
        expires_at=datetime.fromtimestamp(result["expires_at"]),
    )

    if datetime.now() >= session.expires_at:
        await redis_conn.delete(f"session:{session_id}")
        return None

    if datetime.now() >= session.expires_at - timedelta(minutes=30):
        session.expires_at = datetime.now() + timedelta(hours=1)
        session_data = {
            "id": session.id,
            "user_id": session.user_id,
            "expires_at": int(session.expires_at.timestamp()),
        }
        await redis_conn.set(
            f"session:{session.id}",
            json.dumps(session_data),
            exat=int(session.expires_at.timestamp()),
        )

    return session


async def invalidate_session(session_id: str) -> None:
    redis_conn = RedisPool().get_userpanel_connection_async()

    await redis_conn.delete(f"session:{session_id}")


def set_session_token_cookie(response: Response, token: str, expires_at: datetime):
    response.set_cookie(
        "session_token",
        token,
        httponly=True,
        samesite="lax",
        secure=True,
        expires=expires_at,
    )


def delete_session_token_cookie(response: Response):
    response.delete_cookie("session_token")
