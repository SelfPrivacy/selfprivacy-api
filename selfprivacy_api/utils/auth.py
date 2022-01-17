#!/usr/bin/env python3
"""Token management utils"""
import secrets
from datetime import datetime, timedelta
import re

from mnemonic import Mnemonic

from . import ReadUserData, UserDataFiles, WriteUserData

"""
Token are stored in the tokens.json file.
File contains device tokens, recovery token and new device auth token.
File structure:
{
    "tokens": [
        {
            "token": "device token",
            "name": "device name",
            "date": "date of creation",
        }
    ],
    "recovery_token": {
        "token": "recovery token",
        "date": "date of creation",
        "expiration": "date of expiration",
        "uses_left": "number of uses left"
    },
    "new_device": {
        "token": "new device auth token",
        "date": "date of creation",
        "expiration": "date of expiration",
    }
}
Recovery token may or may not have expiration date and uses_left.
There may be no recovery token at all.
Device tokens must be unique.
"""


def _get_tokens():
    """Get all tokens as list of tokens of every device"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        return [token["token"] for token in tokens["tokens"]]


def _get_token_names():
    """Get all token names"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        return [t["name"] for t in tokens["tokens"]]


def _validate_token_name(name):
    """Token name must be an alphanumeric string and not empty.
    Replace invalid characters with '_'
    If token name exists, add a random number to the end of the name until it is unique.
    """
    if not re.match("^[a-zA-Z0-9]*$", name):
        name = re.sub("[^a-zA-Z0-9]", "_", name)
    if name == "":
        name = "Unknown device"
    while name in _get_token_names():
        name += str(secrets.randbelow(10))
    return name


def is_token_valid(token):
    """Check if token is valid"""
    if token in _get_tokens():
        return True
    return False


def is_token_name_exists(token_name):
    """Check if token name exists"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        return token_name in [t["name"] for t in tokens["tokens"]]


def is_token_name_pair_valid(token_name, token):
    """Check if token name and token pair exists"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        for t in tokens["tokens"]:
            if t["name"] == token_name and t["token"] == token:
                return True
        return False


def get_tokens_info():
    """Get all tokens info without tokens themselves"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        return [
            {"name": token["name"], "date": token["date"]} for token in tokens["tokens"]
        ]


def _generate_token():
    """Generates new token and makes sure it is unique"""
    token = secrets.token_urlsafe(32)
    while token in _get_tokens():
        token = secrets.token_urlsafe(32)
    return token


def create_token(name):
    """Create new token"""
    token = _generate_token()
    name = _validate_token_name(name)
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        tokens["tokens"].append(
            {
                "token": token,
                "name": name,
                "date": str(datetime.now()),
            }
        )
    return token


def delete_token(token_name):
    """Delete token"""
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        tokens["tokens"] = [t for t in tokens["tokens"] if t["name"] != token_name]


def refresh_token(token):
    """Change the token field of the existing token"""
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        for t in tokens["tokens"]:
            if t["token"] == token:
                t["token"] = _generate_token()
                break


def is_recovery_token_exists():
    """Check if recovery token exists"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        return "recovery_token" in tokens


def is_recovery_token_valid():
    """Check if recovery token is valid"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "recovery_token" not in tokens:
            return False
        recovery_token = tokens["recovery_token"]
        if "uses_left" in recovery_token:
            if recovery_token["uses_left"] <= 0:
                return False
        if "expiration" not in recovery_token:
            return True
        return datetime.now() < datetime.strptime(
            recovery_token["expiration"], "%Y-%m-%d %H:%M:%S.%f"
        )


def get_recovery_token_status():
    """Get recovery token date of creation, expiration and uses left"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "recovery_token" not in tokens:
            return None
        recovery_token = tokens["recovery_token"]
        return {
            "date": recovery_token["date"],
            "expiration": recovery_token["expiration"]
            if "expiration" in recovery_token
            else None,
            "uses_left": recovery_token["uses_left"]
            if "uses_left" in recovery_token
            else None,
        }


def _get_recovery_token():
    """Get recovery token"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "recovery_token" not in tokens:
            return None
        return tokens["recovery_token"]["token"]


def generate_recovery_token(expiration=None, uses_left=None):
    """Generate a 24 bytes recovery token and return a mneomnic word list.
    Write a string representation of the recovery token to the tokens.json file.
    """
    # expires must be a date or None
    # uses_left must be an integer or None
    if expiration is not None:
        if not isinstance(expiration, datetime):
            raise TypeError("expires must be a datetime object")
    if uses_left is not None:
        if not isinstance(uses_left, int):
            raise TypeError("uses_left must be an integer")
        if uses_left <= 0:
            raise ValueError("uses_left must be greater than 0")

    recovery_token = secrets.token_bytes(24)
    recovery_token_str = recovery_token.hex()
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        tokens["recovery_token"] = {
            "token": recovery_token_str,
            "date": str(datetime.now()),
            "expiration": expiration if expiration is not None else None,
            "uses_left": uses_left if uses_left is not None else None,
        }
    return Mnemonic(language="english").to_mnemonic(recovery_token)


def use_mnemonic_recoverery_token(mnemonic_phrase, name):
    """Use the recovery token by converting the mnemonic word list to a byte array.
    If the recovery token if invalid itself, return None
    If the binary representation of phrase not matches the byte array of the recovery token, return None.
    If the mnemonic phrase is valid then generate a device token and return it.
    Substract 1 from uses_left if it exists.
    mnemonic_phrase is a string representation of the mnemonic word list.
    """
    if not is_recovery_token_valid():
        return None
    recovery_token_str = _get_recovery_token()
    if recovery_token_str is None:
        return None
    recovery_token = bytes.fromhex(recovery_token_str)
    if not Mnemonic(language="english").check(mnemonic_phrase):
        return None
    phrase_bytes = Mnemonic(language="english").to_entropy(mnemonic_phrase)
    if phrase_bytes != recovery_token:
        return None
    token = _generate_token()
    name = _validate_token_name(name)
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        tokens["tokens"].append(
            {
                "token": token,
                "name": name,
                "date": str(datetime.now()),
            }
        )
        if "recovery_token" in tokens:
            if "uses_left" in tokens["recovery_token"]:
                tokens["recovery_token"]["uses_left"] -= 1
    return token


def get_new_device_auth_token():
    """Generate a new device auth token which is valid for 10 minutes and return a mnemonic phrase representation
    Write token to the new_device of the tokens.json file.
    """
    token = secrets.token_bytes(16)
    token_str = token.hex()
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        tokens["new_device"] = {
            "token": token_str,
            "date": str(datetime.now()),
            "expiration": str(datetime.now() + timedelta(minutes=10)),
        }
    return Mnemonic(language="english").to_mnemonic(token)


def _get_new_device_auth_token():
    """Get new device auth token. If it is expired, return None"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "new_device" not in tokens:
            return None
        new_device = tokens["new_device"]
        if "expiration" not in new_device:
            return None
        if datetime.now() > datetime.strptime(
            new_device["expiration"], "%Y-%m-%d %H:%M:%S.%f"
        ):
            return None
        return new_device["token"]


def use_new_device_auth_token(mnemonic_phrase, name):
    """Use the new device auth token by converting the mnemonic string to a byte array.
    If the mnemonic phrase is valid then generate a device token and return it.
    New device auth token must be deleted.
    """
    token_str = _get_new_device_auth_token()
    if token_str is None:
        return None
    token = bytes.fromhex(token_str)
    if not Mnemonic(language="english").check(mnemonic_phrase):
        return None
    phrase_bytes = Mnemonic(language="english").to_entropy(mnemonic_phrase)
    if phrase_bytes != token:
        return None
    token = create_token(name)
    with WriteUserData(UserDataFiles.TOKENS) as tokens:
        if "new_device" in tokens:
            del tokens["new_device"]
    return token
