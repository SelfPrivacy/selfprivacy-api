import pytest
from datetime import datetime, timedelta

from selfprivacy_api.models.tokens.recovery_key import RecoveryKey


def test_recovery_key_expired():
    expiration = datetime.now() - timedelta(minutes=5)
    key = RecoveryKey.generate(expiration=expiration, uses_left=2)
    assert not key.is_valid()
