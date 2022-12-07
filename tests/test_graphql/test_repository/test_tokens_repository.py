# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring

from datetime import datetime, timezone

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
from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from selfprivacy_api.repositories.tokens.redis_tokens_repository import (
    RedisTokensRepository,
)
from tests.common import read_json


ORIGINAL_TOKEN_CONTENT = [
    {
        "token": "KG9ni-B-CMPk327Zv1qC7YBQaUGaBUcgdkvMvQ2atFI",
        "name": "primary_token",
        "date": "2022-07-15 17:41:31.675698",
    },
    {
        "token": "3JKgLOtFu6ZHgE4OU-R-VdW47IKpg-YQL0c6n7bol68",
        "name": "second_token",
        "date": "2022-07-15 17:41:31.675698Z",
    },
    {
        "token": "LYiwFDekvALKTQSjk7vtMQuNP_6wqKuV-9AyMKytI_8",
        "name": "third_token",
        "date": "2022-07-15T17:41:31.675698Z",
    },
    {
        "token": "dD3CFPcEZvapscgzWb7JZTLog7OMkP7NzJeu2fAazXM",
        "name": "forth_token",
        "date": "2022-07-15T17:41:31.675698",
    },
]

ORIGINAL_DEVICE_NAMES = [
    "primary_token",
    "second_token",
    "third_token",
    "forth_token",
]


@pytest.fixture
def tokens(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.TOKENS_FILE", new=datadir / "tokens.json")
    assert read_json(datadir / "tokens.json")["tokens"] == ORIGINAL_TOKEN_CONTENT
    return datadir


@pytest.fixture
def empty_keys(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.TOKENS_FILE", new=datadir / "empty_keys.json")
    assert read_json(datadir / "empty_keys.json")["tokens"] == [
        {
            "token": "KG9ni-B-CMPk327Zv1qC7YBQaUGaBUcgdkvMvQ2atFI",
            "name": "primary_token",
            "date": "2022-07-15 17:41:31.675698",
        }
    ]
    return datadir


@pytest.fixture
def null_keys(mocker, datadir):
    mocker.patch("selfprivacy_api.utils.TOKENS_FILE", new=datadir / "null_keys.json")
    assert read_json(datadir / "null_keys.json")["recovery_token"] is None
    assert read_json(datadir / "null_keys.json")["new_device"] is None
    return datadir


class RecoveryKeyMockReturnNotValid:
    def is_valid() -> bool:
        return False


@pytest.fixture
def mock_new_device_key_generate(mocker):
    mock = mocker.patch(
        "selfprivacy_api.repositories.tokens.json_tokens_repository.NewDeviceKey.generate",
        autospec=True,
        return_value=NewDeviceKey(
            key="43478d05b35e4781598acd76e33832bb",
            created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
            expires_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
        ),
    )
    return mock


@pytest.fixture
def mock_generate_token(mocker):
    mock = mocker.patch(
        "selfprivacy_api.repositories.tokens.json_tokens_repository.Token.generate",
        autospec=True,
        return_value=Token(
            token="ur71mC4aiI6FIYAN--cTL-38rPHS5D6NuB1bgN_qKF4",
            device_name="newdevice",
            created_at=datetime(2022, 11, 14, 6, 6, 32, 777123),
        ),
    )
    return mock


@pytest.fixture
def mock_get_recovery_key_return_not_valid(mocker):
    mock = mocker.patch(
        "selfprivacy_api.repositories.tokens.json_tokens_repository.JsonTokensRepository.get_recovery_key",
        autospec=True,
        return_value=RecoveryKeyMockReturnNotValid,
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
            created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
        ),
    )
    return mock


@pytest.fixture
def mock_recovery_key_generate(mocker):
    mock = mocker.patch(
        "selfprivacy_api.repositories.tokens.json_tokens_repository.RecoveryKey.generate",
        autospec=True,
        return_value=RecoveryKey(
            key="889bf49c1d3199d71a2e704718772bd53a422020334db051",
            created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
            expires_at=None,
            uses_left=1,
        ),
    )
    return mock


@pytest.fixture
def empty_json_repo(tokens):
    repo = JsonTokensRepository()
    for token in repo.get_tokens():
        repo.delete_token(token)
    assert repo.get_tokens() == []
    return repo


@pytest.fixture
def empty_redis_repo():
    repo = RedisTokensRepository()
    for token in repo.get_tokens():
        repo.delete_token(token)
    assert repo.get_tokens() == []
    return repo


@pytest.fixture(params=["json", "redis"])
def empty_repo(request, empty_json_repo):
    if request.param == "json":
        return empty_json_repo
    if request.param == "redis":
        # return empty_redis_repo
        return empty_json_repo
    else:
        raise NotImplementedError


@pytest.fixture
def some_tokens_repo(empty_repo):
    for name in ORIGINAL_DEVICE_NAMES:
        empty_repo.create_token(name)
    assert len(empty_repo.get_tokens()) == len(ORIGINAL_DEVICE_NAMES)
    for i, t in enumerate(empty_repo.get_tokens()):
        assert t.device_name == ORIGINAL_DEVICE_NAMES[i]
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

    assert repo.get_token_by_name(token_name="primary_token") is not None
    assert repo.get_token_by_name(token_name="primary_token") == repo.get_tokens()[0]


def test_get_token_by_non_existent_name(some_tokens_repo):
    repo = some_tokens_repo

    with pytest.raises(TokenNotFound):
        assert repo.get_token_by_name(token_name="badname") is None


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
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )
    assert repo.get_tokens() == [
        Token(
            token="ZuLNKtnxDeq6w2dpOJhbB3iat_sJLPTPl_rN5uc5MvM",
            device_name="IamNewDevice",
            created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
        )
    ]


def test_delete_not_found_token(some_tokens_repo):
    repo = some_tokens_repo
    tokens = repo.get_tokens()
    input_token = Token(
        token="imbadtoken",
        device_name="primary_token",
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )
    with pytest.raises(TokenNotFound):
        assert repo.delete_token(input_token) is None

    assert repo.get_tokens() == tokens


def test_refresh_token(some_tokens_repo, mock_token_generate):
    repo = some_tokens_repo
    input_token = some_tokens_repo.get_tokens()[0]

    assert repo.refresh_token(input_token) == Token(
        token="ZuLNKtnxDeq6w2dpOJhbB3iat_sJLPTPl_rN5uc5MvM",
        device_name="IamNewDevice",
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )


def test_refresh_not_found_token(tokens, mock_token_generate):
    repo = JsonTokensRepository()
    input_token = Token(
        token="idontknowwhoiam",
        device_name="tellmewhoiam?",
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )

    with pytest.raises(TokenNotFound):
        assert repo.refresh_token(input_token) is None


################
# Recovery key #
################


def test_get_recovery_key(tokens):
    repo = JsonTokensRepository()

    assert repo.get_recovery_key() == RecoveryKey(
        key="ed653e4b8b042b841d285fa7a682fa09e925ddb2d8906f54",
        created_at=datetime(2022, 11, 11, 11, 48, 54, 228038),
        expires_at=None,
        uses_left=2,
    )


def test_get_recovery_key_when_empty(empty_keys):
    repo = JsonTokensRepository()

    assert repo.get_recovery_key() is None


def test_create_recovery_key(tokens, mock_recovery_key_generate):
    repo = JsonTokensRepository()

    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None
    # assert read_json(tokens / "tokens.json")["recovery_token"] == {
    #     "token": "889bf49c1d3199d71a2e704718772bd53a422020334db051",
    #     "date": "2022-07-15T17:41:31.675698",
    #     "expiration": None,
    #     "uses_left": 1,
    # }


def test_use_mnemonic_recovery_key_when_empty(
    empty_keys, mock_recovery_key_generate, mock_token_generate
):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_mnemonic_not_valid_recovery_key(
    tokens, mock_get_recovery_key_return_not_valid
):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_mnemonic_not_mnemonic_recovery_key(tokens):
    repo = JsonTokensRepository()

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="sorry, it was joke",
                device_name="primary_token",
            )
            is None
        )


def test_use_not_mnemonic_recovery_key(tokens):
    repo = JsonTokensRepository()

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="please come back",
                device_name="primary_token",
            )
            is None
        )


def test_use_not_found_mnemonic_recovery_key(tokens):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_menemonic_recovery_key_when_empty(empty_keys):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


def test_use_menemonic_recovery_key_when_null(null_keys):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


# agnostic test mixed with an implementation test
def test_use_mnemonic_recovery_key(tokens, mock_generate_token):
    repo = JsonTokensRepository()

    assert repo.use_mnemonic_recovery_key(
        mnemonic_phrase="uniform clarify napkin bid dress search input armor police cross salon because myself uphold slice bamboo hungry park",
        device_name="newdevice",
    ) == Token(
        token="ur71mC4aiI6FIYAN--cTL-38rPHS5D6NuB1bgN_qKF4",
        device_name="newdevice",
        created_at=datetime(2022, 11, 14, 6, 6, 32, 777123),
    )

    # assert read_json(tokens / "tokens.json")["tokens"] == [
    #     {
    #         "date": "2022-07-15 17:41:31.675698",
    #         "name": "primary_token",
    #         "token": "KG9ni-B-CMPk327Zv1qC7YBQaUGaBUcgdkvMvQ2atFI",
    #     },
    #     {
    #         "token": "3JKgLOtFu6ZHgE4OU-R-VdW47IKpg-YQL0c6n7bol68",
    #         "name": "second_token",
    #         "date": "2022-07-15 17:41:31.675698Z",
    #     },
    #     {
    #         "token": "LYiwFDekvALKTQSjk7vtMQuNP_6wqKuV-9AyMKytI_8",
    #         "name": "third_token",
    #         "date": "2022-07-15T17:41:31.675698Z",
    #     },
    #     {
    #         "token": "dD3CFPcEZvapscgzWb7JZTLog7OMkP7NzJeu2fAazXM",
    #         "name": "forth_token",
    #         "date": "2022-07-15T17:41:31.675698",
    #     },
    #     {
    #         "date": "2022-11-14T06:06:32.777123",
    #         "name": "newdevice",
    #         "token": "ur71mC4aiI6FIYAN--cTL-38rPHS5D6NuB1bgN_qKF4",
    #     },
    # ]

    # assert read_json(tokens / "tokens.json")["recovery_token"] == {
    #     "date": "2022-11-11T11:48:54.228038",
    #     "expiration": None,
    #     "token": "ed653e4b8b042b841d285fa7a682fa09e925ddb2d8906f54",
    #     "uses_left": 1,
    # }


##################
# New device key #
##################


def test_get_new_device_key(tokens, mock_new_device_key_generate):
    repo = JsonTokensRepository()

    assert repo.get_new_device_key() is not None
    # assert read_json(tokens / "tokens.json")["new_device"] == {
    #     "date": "2022-07-15T17:41:31.675698",
    #     "expiration": "2022-07-15T17:41:31.675698",
    #     "token": "43478d05b35e4781598acd76e33832bb",
    # }


def test_delete_new_device_key(tokens):
    repo = JsonTokensRepository()

    assert repo.delete_new_device_key() is None
    # assert "new_device" not in read_json(tokens / "tokens.json")


def test_delete_new_device_key_when_empty(empty_keys):
    repo = JsonTokensRepository()

    repo.delete_new_device_key()
    # assert "new_device" not in read_json(empty_keys / "empty_keys.json")


def test_use_invalid_mnemonic_new_device_key(
    tokens, mock_new_device_key_generate, datadir, mock_token_generate
):
    repo = JsonTokensRepository()

    with pytest.raises(InvalidMnemonic):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="oh-no",
            )
            is None
        )


def test_use_not_exists_mnemonic_new_device_key(
    tokens, mock_new_device_key_generate, mock_token_generate
):
    repo = JsonTokensRepository()

    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="uniform clarify napkin bid dress search input armor police cross salon because myself uphold slice bamboo hungry park",
            )
            is None
        )


def test_use_mnemonic_new_device_key(
    tokens, mock_new_device_key_generate, mock_token_generate
):
    repo = JsonTokensRepository()

    assert (
        repo.use_mnemonic_new_device_key(
            device_name="imnew",
            mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
        )
        is not None
    )
    # assert read_json(datadir / "tokens.json")["new_device"] == []


def test_use_mnemonic_new_device_key_when_empty(empty_keys):
    repo = JsonTokensRepository()

    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
            )
            is None
        )


def test_use_mnemonic_new_device_key_when_null(null_keys):
    repo = JsonTokensRepository()

    with pytest.raises(NewDeviceKeyNotFound):
        assert (
            repo.use_mnemonic_new_device_key(
                device_name="imnew",
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
            )
            is None
        )
