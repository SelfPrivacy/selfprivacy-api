import stat

from pytest import fixture

from selfprivacy_api.backup.local_secret import LocalBackupSecret


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


def test_password_file_is_root_only(mocker, tmp_path):
    password_file = tmp_path / "restic-password"
    mocker.patch(
        "selfprivacy_api.backup.local_secret.RESTIC_PASSWORD_FILE", str(password_file)
    )
    mocker.patch.object(LocalBackupSecret, "get", return_value="; touch /tmp/pwned #")

    assert LocalBackupSecret.password_file() == str(password_file)
    assert password_file.read_text() == "; touch /tmp/pwned #\n"
    assert stat.S_IMODE(password_file.stat().st_mode) == 0o600
