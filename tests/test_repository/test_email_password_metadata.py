import uuid
from datetime import datetime, timedelta, timezone

import pytest

from selfprivacy_api.models.email_password_metadata import EmailPasswordData
from selfprivacy_api.repositories.email_password.email_password_redis_repository import (
    EmailPasswordManager,
)
from selfprivacy_api.utils.redis_pool import RedisPool


def create_password_metadata() -> EmailPasswordData:
    now = datetime.now(timezone.utc)

    return EmailPasswordData(
        uuid=uuid.uuid4().hex,
        display_name="Test",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        password=None,
        last_used=None,
    )


def _check_metadata(user, metadata, redis):
    key = f"priv/user/{user}/passwords/{metadata.uuid}"
    stored = redis.hgetall(key)

    assert stored["password"] == "hash123"
    assert stored["display_name"] == metadata.display_name
    assert stored["created_at"] == metadata.created_at.isoformat()
    assert stored["expires_at"] == metadata.expires_at.isoformat()


def get_test_user() -> str:
    return f"test_{uuid.uuid4().hex}"


def test_add_email_password_hash():
    test_user = get_test_user()
    metadata = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash123", metadata)

    redis = RedisPool().get_userpanel_connection()

    _check_metadata(test_user, metadata, redis)


def test_add_multiple_email_password_hash_for_one_user():
    test_user = get_test_user()
    metadata1 = create_password_metadata()
    metadata2 = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash123", metadata1)
    EmailPasswordManager.add_email_password_hash(test_user, "hash123", metadata2)

    redis = RedisPool().get_userpanel_connection()

    _check_metadata(test_user, metadata1, redis)
    _check_metadata(test_user, metadata2, redis)


def test_get_all_email_passwords_no_hashes():
    metadata1 = create_password_metadata()
    metadata2 = create_password_metadata()
    test_user = get_test_user()

    EmailPasswordManager.add_email_password_hash(test_user, "hash1", metadata1)
    EmailPasswordManager.add_email_password_hash(test_user, "hash2", metadata2)

    result = EmailPasswordManager.get_all_email_passwords_metadata(test_user)

    uuids = {r.uuid for r in result}

    assert uuids == {metadata1.uuid, metadata2.uuid}
    for item in result:
        assert item.password is None


def test_get_all_email_passwords_no_hashes_nonexist_user():
    test_user = get_test_user()

    result = EmailPasswordManager.get_all_email_passwords_metadata(test_user)

    assert isinstance(result, list)
    assert result == []


def test_get_all_email_passwords_with_hashes():
    test_user = get_test_user()
    metadata = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash", metadata)

    result = EmailPasswordManager.get_all_email_passwords_metadata(
        test_user, with_passwords_hashes=True
    )

    assert len(result) == 1
    assert result[0].password == "hash"


def test_update_email_password_hash_last_used():
    test_user = get_test_user()
    metadata = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash", metadata)
    EmailPasswordManager.update_email_password_hash_last_used(test_user, metadata.uuid)

    redis = RedisPool().get_userpanel_connection()
    key = f"priv/user/{test_user}/passwords/{metadata.uuid}"
    last_used_str = redis.hget(key, "last_used")

    assert last_used_str is not None
    last_used_dt = datetime.fromisoformat(last_used_str)

    assert datetime.now(timezone.utc) - last_used_dt < timedelta(seconds=3)


def test_update_nonexisting_email_password_hash_last_used():
    test_user = get_test_user()
    nonexising_user = get_test_user()
    metadata = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash", metadata)
    EmailPasswordManager.update_email_password_hash_last_used(
        nonexising_user, metadata.uuid
    )

    redis = RedisPool().get_userpanel_connection()
    key = f"priv/user/{test_user}/passwords/{metadata.uuid}"
    last_used_str = redis.hget(key, "last_used")

    assert last_used_str is None


def test_delete_email_password_hash():
    test_user = get_test_user()
    meta = create_password_metadata()

    EmailPasswordManager.add_email_password_hash(test_user, "hash", meta)
    EmailPasswordManager.delete_email_password_hash(test_user, meta.uuid)

    redis = RedisPool().get_userpanel_connection()
    key = f"priv/user/{test_user}/passwords/{meta.uuid}"

    assert not redis.exists(key)


def test_delete_all_email_passwords_hashes():
    test_user = get_test_user()

    for _ in range(3):
        meta = create_password_metadata()
        EmailPasswordManager.add_email_password_hash(test_user, "hash", meta)

    EmailPasswordManager.delete_all_email_passwords_hashes(test_user)

    redis = RedisPool().get_userpanel_connection()
    keys_in_db = redis.keys(f"priv/user/{test_user}/passwords/*")

    assert keys_in_db == []
