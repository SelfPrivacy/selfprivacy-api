from selfprivacy_api.backup.local_secret import LocalBackupSecret
from pytest import fixture


@fixture()
def localsecret():
    LocalBackupSecret._full_reset()
    return LocalBackupSecret


def test_local_secret_firstget(localsecret):
    assert not LocalBackupSecret.exists()
    secret = LocalBackupSecret.get()
    assert LocalBackupSecret.exists()
    assert secret is not None

    # making sure it does not reset again
    secret2 = LocalBackupSecret.get()
    assert LocalBackupSecret.exists()
    assert secret2 == secret


def test_local_secret_reset(localsecret):
    secret1 = LocalBackupSecret.get()

    LocalBackupSecret.reset()
    secret2 = LocalBackupSecret.get()
    assert secret2 is not None
    assert secret2 != secret1


def test_local_secret_set(localsecret):
    newsecret = "great and totally safe secret"
    oldsecret = LocalBackupSecret.get()
    assert oldsecret != newsecret

    LocalBackupSecret.set(newsecret)
    assert LocalBackupSecret.get() == newsecret
