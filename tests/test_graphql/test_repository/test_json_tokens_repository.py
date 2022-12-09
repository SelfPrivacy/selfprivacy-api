# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
"""
tests that restrict json token repository implementation
"""

import pytest


from datetime import datetime

from selfprivacy_api.models.tokens.token import Token
from selfprivacy_api.repositories.tokens.exceptions import (
    TokenNotFound,
    RecoveryKeyNotFound,
    NewDeviceKeyNotFound,
)
from selfprivacy_api.repositories.tokens.json_tokens_repository import (
    JsonTokensRepository,
)
from tests.common import read_json

from test_tokens_repository import ORIGINAL_TOKEN_CONTENT
from test_tokens_repository import (
    tokens,
    mock_recovery_key_generate,
    mock_generate_token,
    mock_new_device_key_generate,
    empty_keys,
    null_keys,
)


def test_delete_token(tokens):
    repo = JsonTokensRepository()
    input_token = Token(
        token="KG9ni-B-CMPk327Zv1qC7YBQaUGaBUcgdkvMvQ2atFI",
        device_name="primary_token",
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )

    repo.delete_token(input_token)
    assert read_json(tokens / "tokens.json")["tokens"] == [
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


def test_delete_not_found_token(tokens):
    repo = JsonTokensRepository()
    input_token = Token(
        token="imbadtoken",
        device_name="primary_token",
        created_at=datetime(2022, 7, 15, 17, 41, 31, 675698),
    )
    with pytest.raises(TokenNotFound):
        assert repo.delete_token(input_token) is None

    assert read_json(tokens / "tokens.json")["tokens"] == ORIGINAL_TOKEN_CONTENT


def test_create_recovery_key(tokens, mock_recovery_key_generate):
    repo = JsonTokensRepository()

    assert repo.create_recovery_key(uses_left=1, expiration=None) is not None
    assert read_json(tokens / "tokens.json")["recovery_token"] == {
        "token": "889bf49c1d3199d71a2e704718772bd53a422020334db051",
        "date": "2022-07-15T17:41:31.675698",
        "expiration": None,
        "uses_left": 1,
    }


def test_use_mnemonic_recovery_key_when_null(null_keys):
    repo = JsonTokensRepository()

    with pytest.raises(RecoveryKeyNotFound):
        assert (
            repo.use_mnemonic_recovery_key(
                mnemonic_phrase="captain ribbon toddler settle symbol minute step broccoli bless universe divide bulb",
                device_name="primary_token",
            )
            is None
        )


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

    assert read_json(tokens / "tokens.json")["tokens"] == [
        {
            "date": "2022-07-15 17:41:31.675698",
            "name": "primary_token",
            "token": "KG9ni-B-CMPk327Zv1qC7YBQaUGaBUcgdkvMvQ2atFI",
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
        {
            "date": "2022-11-14T06:06:32.777123",
            "name": "newdevice",
            "token": "ur71mC4aiI6FIYAN--cTL-38rPHS5D6NuB1bgN_qKF4",
        },
    ]
    assert read_json(tokens / "tokens.json")["recovery_token"] == {
        "date": "2022-11-11T11:48:54.228038",
        "expiration": None,
        "token": "ed653e4b8b042b841d285fa7a682fa09e925ddb2d8906f54",
        "uses_left": 1,
    }


def test_get_new_device_key(tokens, mock_new_device_key_generate):
    repo = JsonTokensRepository()

    assert repo.get_new_device_key() is not None
    assert read_json(tokens / "tokens.json")["new_device"] == {
        "date": "2022-07-15T17:41:31.675698",
        "expiration": "2022-07-15T17:41:31.675698",
        "token": "43478d05b35e4781598acd76e33832bb",
    }


def test_delete_new_device_key(tokens):
    repo = JsonTokensRepository()

    assert repo.delete_new_device_key() is None
    assert "new_device" not in read_json(tokens / "tokens.json")


def test_delete_new_device_key_when_empty(empty_keys):
    repo = JsonTokensRepository()

    repo.delete_new_device_key()
    assert "new_device" not in read_json(empty_keys / "empty_keys.json")


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
