#!/usr/bin/env python3
"""Token management utils"""
import secrets
from datetime import datetime, timedelta
import re
import typing

from pydantic import BaseModel
from mnemonic import Mnemonic

from . import ReadUserData, UserDataFiles, WriteUserData, parse_date

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


class BasicTokenInfo(BaseModel):
    """Token info"""

    name: str
    date: datetime


def _generate_token():
    """Generates new token and makes sure it is unique"""
    token = secrets.token_urlsafe(32)
    while token in _get_tokens():
        token = secrets.token_urlsafe(32)
    return token


def _get_recovery_token():
    """Get recovery token"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "recovery_token" not in tokens:
            return None
        return tokens["recovery_token"]["token"]


def _get_new_device_auth_token():
    """Get new device auth token. If it is expired, return None"""
    with ReadUserData(UserDataFiles.TOKENS) as tokens:
        if "new_device" not in tokens:
            return None
        new_device = tokens["new_device"]
        if "expiration" not in new_device:
            return None
        expiration = parse_date(new_device["expiration"])
        if datetime.now() > expiration:
            return None
        return new_device["token"]
