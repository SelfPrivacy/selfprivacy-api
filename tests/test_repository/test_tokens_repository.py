# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from datetime import datetime, timezone
from mnemonic import Mnemonic

import pytest

from selfprivacy_api.models.tokens.new_device_key import NewDeviceKey
from selfprivacy_api.models.tokens.recovery_key import RecoveryKey
from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.exceptions import (
    InvalidMnemonic,
    RecoveryKeyNotFound,
    TokenNotFound,
    NewDeviceKeyNotFound,
)

from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)
from selfprivacy_api.repositories.tokens.abstract_tokens_repository import (
    AbstractTokensRepository,
)

from tests.common import ten_minutes_into_past, ten_hours_into_future


ORIGINAL_DEVICE_NAMES = [
    "primary_token",
    "second_token",
    "third_token",
    "forth_token",
]

TEST_DATE = datetime(2022, 7, 15, 17, 41, 31, 675698, timezone.utc)
# tokens are not tz-aware
TOKEN_TEST_DATE = datetime(2022, 7, 15, 17, 41, 31, 675698)


def mnemonic_from_hex(hexkey):
    return Mnemonic(language="english").to_mnemonic(bytes.fromhex(hexkey))


@pytest.fixture
def mock_new_device_key_generate(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.new_device_key.NewDeviceKey.generate",
        autospec=True,
        return_value=NewDeviceKey(
            key="43478d05b35e4781598acd76e33832bb",
            created_at=TEST_DATE,
            expires_at=TEST_DATE,
        ),
    )
    return mock


# mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
@pytest.fixture
def mock_new_device_key_generate_for_mnemonic(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.new_device_key.NewDeviceKey.generate",
        autospec=True,
        return_value=NewDeviceKey(
            key="2237238de23dc71ab558e317bdb8ff8e",
            created_at=TEST_DATE,
            expires_at=TEST_DATE,
        ),
    )
    return mock


@pytest.fixture
def mock_generate_token(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.token.Token.generate",
        autospec=True,
        return_value=Token(
            token="ur71mC4aiI6FIYAN--cTL-38rPHS5D6NuB1bgN_qKF4",
            device_name="newdevice",
            created_at=datetime(2022, 11, 14, 6, 6, 32, 777123),
        ),
    )
    return mock


@pytest.fixture
def mock_recovery_key_generate_invalid(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.recovery_key.RecoveryKey.generate",
        autospec=True,
        return_value=RecoveryKey(
            key="889bf49c1d3199d71a2e704718772bd53a422020334db051",
            created_at=TEST_DATE,
            expires_at=None,
            uses_left=0,
        ),
    )
    return mock


@pytest.fixture
def mock_token_generate(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.token.Token.generate",
        autospec=True,
        return_value=Token(
            token="ZuLNKtnxDeq6w2dpOJhbB3iat_sJLPTPl_rN5uc5MvM",
            device_name="IamNewDevice",
            created_at=TOKEN_TEST_DATE,
        ),
    )
    return mock


@pytest.fixture
def mock_recovery_key_generate(mocker):
    mock = mocker.patch(
        "selfprivacy_api.models.tokens.recovery_key.RecoveryKey.generate",
        autospec=True,
        return_value=RecoveryKey(
            key="889bf49c1d3199d71a2e704718772bd53a422020334db051",
            created_at=TEST_DATE,
            expires_at=None,
            uses_left=1,
        ),
    )
    return mock


@pytest.fixture(params=["redis"])
def empty_repo(request, empty_redis_repo):
    if request.param == "redis":
        return empty_redis_repo
        # return empty_json_repo
    else:
        raise NotImplementedError


@pytest.fixture
def some_tokens_repo(empty_repo):
    for name in ORIGINAL_DEVICE_NAMES:
        empty_repo.create_token(name)
    assert len(empty_repo.get_tokens()) == len(ORIGINAL_DEVICE_NAMES)
    for name in ORIGINAL_DEVICE_NAMES:
        assert empty_repo.get_token_by_name(name) is not None
    assert empty_repo.get_new_device_key() is not None
    return empty_repo


###############
# Test tokens #
###############


def test_get_token_by_token_string(some_tokens_repo):
    repo = some_tokens_repo
    test_token = repo.get_tokens()[2]

    assert repo.get_token_by_token_string(token_string=test_token.token) == test_token


def test_get_token_by_non_existent_token_string(some_tokens_repo):
    repo = some_tokens_repo

    with pytest.raises(TokenNotFound):
        assert repo.get_token_by_token_string(token_string="iamBadtoken") is None


def test_get_token_by_name(some_tokens_repo):
    repo = some_tokens_repo

    token = repo.get_token_by_name(token_name="primary_token")
    assert token is not None
    assert token.device_name == "primary_token"
    assert token in repo.get_tokens()


def test_get_token_by_non_existent_name(some_tokens_repo):
    repo = some_tokens_repo

    with pytest.raises(TokenNotFound):
        assert repo.get_token_by_name(token_name="badname") is None


def test_is_token_valid(some_tokens_repo):
    repo = some_tokens_repo
    token = repo.get_tokens()[0]
    assert repo.is_token_valid(token.token)
    assert not repo.is_token_valid("gibberish")


def test_is_token_name_pair_valid(some_tokens_repo):
    repo = some_tokens_repo
    token = repo.get_tokens()[0]
    assert repo.is_token_name_pair_valid(token.device_name, token.token)
    assert not repo.is_token_name_pair_valid(token.device_name, "gibberish")
    assert not repo.is_token_name_pair_valid("gibberish", token.token)


def test_is_token_name_exists(some_tokens_repo):
    repo = some_tokens_repo
    token = repo.get_tokens()[0]
    assert repo.is_token_name_exists(token.device_name)
    assert not repo.is_token_name_exists("gibberish")


def test_get_tokens(some_tokens_repo):
    repo = some_tokens_repo
    tokenstrings = []
    # we cannot insert tokens directly via api, so we check meta-properties instead
    for token in repo.get_tokens():
        len(token.token) == 43  # assuming secrets.token_urlsafe
        assert token.token not in tokenstrings
        tokenstrings.append(token.token)
        assert token.created_at.day == datetime.today().day


def test_create_token(empty_repo, mock_token_generate):
    repo = empty_repo

    assert repo.create_token(device_name="IamNewDevice") == Token(
        token="ZuLNKtnxDeq6w2dpOJhbB3iat_sJLPTPl_rN5uc5MvM",
        device_name="IamNewDevice",
        created_at=TOKEN_TEST_DATE,
    )
    assert repo.get_tokens() == [
        Token(
            token="ZuLNKtnxDeq6w2dpOJhbB3iat_sJLPTPl_rN5uc5MvM",
            device_name="IamNewDevice",
            created_at=TOKEN_TEST_DATE,
        )
    ]


def test_create_token_existing(some_tokens_repo):
    repo = some_tokens_repo
    old_token = repo.get_tokens()[0]

    new_token = repo.create_token(device_name=old_token.device_name)
    assert new_token.device_name != old_token.device_name

    assert old_token in repo.get_tokens()
    assert new_token in repo.get_tokens()


def test_delete_token(some_tokens_repo):
    repo = some_tokens_repo
    original_tokens = repo.get_tokens()
    input_token = original_tokens[1]

    repo.delete_token(input_token)

    tokens_after_delete = repo.get_tokens()
    for token in original_tokens:
        if token != input_token:
            assert token in tokens_after_delete
    assert len(original_tokens) == len(tokens_after_delete) + 1


def test_delete_not_found_token(some_tokens_repo):
    repo = some_tokens_repo
    initial_tokens = repo.get_tokens()
    input_token = Token(
        token="imbadtoken",
        device_name="primary_token",
        created_at=TEST_DATE,
    )
    with pytest.raises(TokenNotFound):
        assert repo.delete_token(input_token) is None

    new_tokens = repo.get_tokens()
    assert len(new_tokens) == len(initial_tokens)
    for token in initial_tokens:
        assert token in new_tokens


def test_refresh_token(some_tokens_repo):
    repo = some_tokens_repo
    input_token = some_tokens_repo.get_tokens()[0]

    output_token = repo.refresh_token(input_token)

    assert output_token.token != input_token.token
    assert output_token.device_name == input_token.device_name
    assert output_token.created_at == input_token.created_at

    assert output_token in repo.get_tokens()


def test_refresh_not_found_token(some_tokens_repo, mock_token_generate):
    repo = some_tokens_repo
    input_token = Token(
        token="idontknowwhoiam",
        device_name="tellmewhoiam?",
        created_at=TEST_DATE,
    )

    with pytest.raises(TokenNotFound):
        assert repo.refresh_token(input_token) is None


################
# Recovery key #
################


def test_get_recovery_key_when_empty(empty_repo):
    repo = empty_repo

    assert repo.get_recovery_key() is None


def test_create_get_recovery_key(some_tokens_repo, mock_recovery_key_generate):
    repo = some_tokens_repo

    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None
    assert repo.get_recovery_key() == RecoveryKey(
        key="889bf49c1d3199d71a2e704718772bd53a422020334db051",
        created_at=TEST_DATE,
        expires_at=None,
        uses_left=1,
    )


def test_use_mnemonic_recovery_key_when_empty(empty_repo):
    repo = empty_repo

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_mnemonic_not_valid_recovery_key(
    some_tokens_repo, mock_recovery_key_generate_invalid
):
    repo = some_tokens_repo
    assert repo.create_recovery_key(uses_left=0, expiration=None) is not None

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_mnemonic_expired_recovery_key(
    some_tokens_repo,
):
    repo = some_tokens_repo
    expiration = ten_minutes_into_past()
    assert repo.create_recovery_key(uses_left=2, expiration=expiration) is not None
    recovery_key = repo.get_recovery_key()
    # TODO: do not ignore timezone once json backend is deleted
    assert recovery_key.expires_at.replace(tzinfo=None) == expiration.replace(
        tzinfo=None
    )
    assert not repo.is_recovery_key_valid()

    with pytest.raises(RecoveryKeyNotFound):
        token = repo.use_mnemonic_recovery_key(
            mnemonic_phrase=mnemonic_from_hex(recovery_key.key),
            device_name="newdevice",
        )


def test_use_mnemonic_not_mnemonic_recovery_key(some_tokens_repo):
    repo = some_tokens_repo
    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="sorry, it was joke",
                device_name="primary_token",
            )
            is None
        )


def test_use_not_mnemonic_recovery_key(some_tokens_repo):
    repo = some_tokens_repo
    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="please come back",
                device_name="primary_token",
            )
            is None
        )


def test_use_not_found_mnemonic_recovery_key(some_tokens_repo):
    repo = some_tokens_repo
    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


@pytest.fixture(params=["recovery_uses_1", "recovery_eternal"])
def recovery_key_uses_left(request):
    if request.param == "recovery_uses_1":
        return 1
    if request.param == "recovery_eternal":
        return None


def test_use_mnemonic_recovery_key(some_tokens_repo, recovery_key_uses_left):
    repo = some_tokens_repo
    assert (
        repo.create_recovery_key(uses_left=recovery_key_uses_left, expiration=None)
        is not None
    )
    assert repo.is_recovery_key_valid()
    recovery_key = repo.get_recovery_key()

    token = repo.use_mnemonic_recovery_key(
        mnemonic_phrase=mnemonic_from_hex(recovery_key.key),
        device_name="newdevice",
    )

    assert token.device_name == "newdevice"
    assert token in repo.get_tokens()
    new_uses = None
    if recovery_key_uses_left is not None:
        new_uses = recovery_key_uses_left - 1
    assert repo.get_recovery_key() == RecoveryKey(
        key=recovery_key.key,
        created_at=recovery_key.created_at,
        expires_at=None,
        uses_left=new_uses,
    )


##################
# New device key #
##################


def test_get_new_device_key(some_tokens_repo, mock_new_device_key_generate):
    repo = some_tokens_repo

    assert repo.get_new_device_key() == NewDeviceKey(
        key="43478d05b35e4781598acd76e33832bb",
        created_at=TEST_DATE,
        expires_at=TEST_DATE,
    )


def test_delete_new_device_key(some_tokens_repo):
    repo = some_tokens_repo

    assert repo.delete_new_device_key() is None
    # we cannot say if there is ot not without creating it?


def test_delete_new_device_key_when_empty(empty_repo):
    repo = empty_repo

    assert repo.delete_new_device_key() is None


def test_use_invalid_mnemonic_new_device_key(some_tokens_repo):
    repo = some_tokens_repo

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="oh-no",
            )
            is None
        )


def test_use_not_exists_mnemonic_new_device_key(
    empty_repo, mock_new_device_key_generate
):
    repo = empty_repo
    assert repo.get_new_device_key() is not None

    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="uniform clarify napkin bid dress search input armor police cross salon because myself uphold slice bamboo hungry park",
            )
            is None
        )


def test_use_mnemonic_new_device_key(empty_repo):
    repo = empty_repo
    key = repo.get_new_device_key()
    assert key is not None

    mnemonic_phrase = mnemonic_from_hex(key.key)

    new_token = repo.use_mnemonic_new_device_key(
        device_name="imnew",
        mnemonic_phrase=mnemonic_phrase,
    )

    assert new_token.device_name == "imnew"
    assert new_token in repo.get_tokens()

    # we must delete the key after use
    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase=mnemonic_phrase,
            )
            is None
        )


def test_use_mnemonic_expired_new_device_key(
    some_tokens_repo,
):
    repo = some_tokens_repo
    expiration = ten_minutes_into_past()

    key = repo.get_new_device_key()
    assert key is not None
    assert key.expires_at is not None
    key.expires_at = expiration
    assert not key.is_valid()
    repo._store_new_device_key(key)

    with pytest.raises(NewDeviceKeyNotFound):
        token = repo.use_mnemonic_new_device_key(
            mnemonic_phrase=mnemonic_from_hex(key.key),
            device_name="imnew",
        )


def test_use_mnemonic_new_device_key_when_empty(empty_repo):
    repo = empty_repo

    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
            )
            is None
        )


def assert_identical(
    repo_a: AbstractTokensRepository, repo_b: AbstractTokensRepository
):
    tokens_a = repo_a.get_tokens()
    tokens_b = repo_b.get_tokens()
    assert len(tokens_a) == len(tokens_b)
    for token in tokens_a:
        assert token in tokens_b
    assert repo_a.get_recovery_key() == repo_b.get_recovery_key()
    assert repo_a._get_stored_new_device_key() == repo_b._get_stored_new_device_key()
