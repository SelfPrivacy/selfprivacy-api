import pytest
from datetime import datetime, timedelta, timezone

from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey


def test_recovery_key_expired_utcnaive():
    expiration = datetime.utcnow() - timedelta(minutes=5)
    key = RecoveryKey.generate(expiration=expiration, uses_left=2)
    assert not key.is_valid()


def test_recovery_key_expired_tzaware():
    expiration = datetime.now(timezone.utc) - timedelta(minutes=5)
    key = RecoveryKey.generate(expiration=expiration, uses_left=2)
    assert not key.is_valid()


def test_new_device_key_expired():
    # key is supposed to be tzaware
    expiration = datetime.now(timezone.utc) - timedelta(minutes=5)
    key = NewDeviceKey.generate()
    key.expires_at = expiration
    assert not key.is_valid()
