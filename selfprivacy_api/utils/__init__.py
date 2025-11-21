#!/usr/bin/env python3
"""Various utility functions"""
import datetime
from enum import Enum
from typing import Callable, TypeVar
import json
import os
import subprocess
import portalocker
from typing import Optional
import glob
from contextlib import contextmanager

from traceback import format_tb as format_traceback

from selfprivacy_api.utils.default_subdomains import (
    DEFAULT_SUBDOMAINS,
    RESERVED_SUBDOMAINS,
)


USERDATA_FILE = "/etc/nixos/userdata.json"
SECRETS_FILE = "/etc/selfprivacy/secrets.json"
DKIM_DIR = "/var/dkim"

ACCOUNT_PATH_PATTERN = (
    "/var/lib/acme/.lego/accounts/*/acme-v02.api.letsencrypt.org/*/account.json"
)


class UserDataFiles(Enum):
    """Enum for userdata files"""

    USERDATA = 0
    SECRETS = 3


def get_domain():
    """Get domain from userdata.json"""
    with ReadUserData() as user_data:
        return user_data["domain"]


class WriteUserData(object):
    """Write userdata.json with lock"""

    def __init__(self, file_type=UserDataFiles.USERDATA):
        if file_type == UserDataFiles.USERDATA:
            self.userdata_file = open(USERDATA_FILE, "r+", encoding="utf-8")
        elif file_type == UserDataFiles.SECRETS:
            # Make sure file exists
            if not os.path.exists(SECRETS_FILE):
                with open(SECRETS_FILE, "w", encoding="utf-8") as secrets_file:
                    secrets_file.write("{}")
            self.userdata_file = open(SECRETS_FILE, "r+", encoding="utf-8")
        else:
            raise ValueError("Unknown file type")
        portalocker.lock(self.userdata_file, portalocker.LOCK_EX)
        self.data = json.load(self.userdata_file)

    def __enter__(self):
        return self.data

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.userdata_file.seek(0)
            json.dump(self.data, self.userdata_file, indent=4)
            self.userdata_file.truncate()
        portalocker.unlock(self.userdata_file)
        self.userdata_file.close()


class ReadUserData(object):
    """Read userdata.json with lock"""

    def __init__(self, file_type=UserDataFiles.USERDATA):
        if file_type == UserDataFiles.USERDATA:
            self.userdata_file = open(USERDATA_FILE, "r", encoding="utf-8")
        elif file_type == UserDataFiles.SECRETS:
            if not os.path.exists(SECRETS_FILE):
                with open(SECRETS_FILE, "w", encoding="utf-8") as secrets_file:
                    secrets_file.write("{}")
            self.userdata_file = open(SECRETS_FILE, "r", encoding="utf-8")
        else:
            raise ValueError("Unknown file type")
        portalocker.lock(self.userdata_file, portalocker.LOCK_SH)
        self.data = json.load(self.userdata_file)

    def __enter__(self) -> dict:
        return self.data

    def __exit__(self, *args):
        portalocker.unlock(self.userdata_file)
        self.userdata_file.close()


def ensure_ssh_and_users_fields_exist(data):
    if "ssh" not in data:
        data["ssh"] = {}
        data["ssh"]["rootKeys"] = []

    elif data["ssh"].get("rootKeys") is None:
        data["ssh"]["rootKeys"] = []

    if "sshKeys" not in data:
        data["sshKeys"] = []

    if "users" not in data:
        data["users"] = []


def validate_ssh_public_key(key):
    """Validate SSH public key.
    It may be ssh-ed25519, ssh-rsa or ecdsa-sha2-nistp256."""
    if not key.startswith("ssh-ed25519"):
        if not key.startswith("ssh-rsa"):
            if not key.startswith("ecdsa-sha2-nistp256"):
                return False
    return True


def is_username_forbidden(username):
    forbidden_prefixes = ["systemd", "nixbld"]

    forbidden_usernames = [
        "root",
        "messagebus",
        "postfix",
        "polkituser",
        "dovecot2",
        "dovenull",
        "nginx",
        "postgres",
        "prosody",
        "opendkim",
        "rspamd",
        "sshd",
        "selfprivacy-api",
        "restic",
        "redis",
        "pleroma",
        "ocserv",
        "nextcloud",
        "memcached",
        "knot-resolver",
        "gitea",
        "bitwarden_rs",
        "vaultwarden",
        "acme",
        "virtualMail",
        "nobody",
    ]

    for prefix in forbidden_prefixes:
        if username.startswith(prefix):
            return True

    for forbidden_username in forbidden_usernames:
        if username == forbidden_username:
            return True

    return False


def check_if_subdomain_is_taken(subdomain: str) -> bool:
    """Check if subdomain is already taken or reserved"""
    if subdomain in RESERVED_SUBDOMAINS:
        return True
    with ReadUserData() as data:
        for module in data["modules"]:
            if (
                data["modules"][module].get(
                    "subdomain", DEFAULT_SUBDOMAINS.get(module, "")
                )
                == subdomain
            ):
                return True
    return False


def parse_date(date_str: str) -> datetime.datetime:
    """Parse date string which can be in one of these formats:
    - %Y-%m-%dT%H:%M:%S.%fZ
    - %Y-%m-%dT%H:%M:%S.%f
    - %Y-%m-%d %H:%M:%S.%fZ
    - %Y-%m-%d %H:%M:%S.%f
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%fZ")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        pass
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        pass
    raise ValueError("Invalid date string")


def parse_dkim(dkim: str) -> str:
    # extract key from file
    dkim = dkim.split("(")[1]
    dkim = dkim.split(")")[0]
    # replace all quotes with nothing
    dkim = dkim.replace('"', "")
    # trim whitespace, remove newlines and tabs
    dkim = dkim.strip()
    dkim = dkim.replace("\n", "")
    dkim = dkim.replace("\t", "")
    # remove all redundant spaces
    dkim = " ".join(dkim.split())
    return dkim


def get_dkim_key(domain: str, parse: bool = True) -> Optional[str]:
    """Get DKIM key from /var/dkim/<domain>.selector.txt"""

    dkim_path = os.path.join(DKIM_DIR, domain + ".selector.txt")
    if os.path.exists(dkim_path):
        with open(dkim_path, encoding="utf-8") as dkim_file:
            dkim = dkim_file.read()
            if parse:
                dkim = parse_dkim(dkim)
        return dkim
    return None


def hash_password(password):
    hashing_command = ["mkpasswd", "-m", "sha-512", password]
    password_hash_process_descriptor = subprocess.Popen(
        hashing_command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    hashed_password = password_hash_process_descriptor.communicate()[0]
    hashed_password = hashed_password.decode("ascii")
    hashed_password = hashed_password.rstrip()
    return hashed_password


def write_to_log(message):
    with open("/etc/selfprivacy/log", "a") as log:
        log.write(f"{datetime.datetime.now()} {message}\n")
        log.flush()
        os.fsync(log.fileno())


def pretty_error(e: Exception) -> str:
    traceback = "/r".join(format_traceback(e.__traceback__))
    return type(e).__name__ + ": " + str(e) + ": " + traceback


def read_account_uri() -> str:
    account_file = glob.glob(ACCOUNT_PATH_PATTERN)

    if not account_file:
        raise FileNotFoundError(
            f"No account files found matching: {ACCOUNT_PATH_PATTERN}"
        )

    account_file = list(account_file)

    # Sometimes LEGO creates new ACME account, so API gets confused. Let's always just use last created one.
    account_file.sort(key=os.path.getctime, reverse=True)

    with open(account_file[0], "r") as file:
        account_info = json.load(file)
        return account_info["registration"]["uri"]


@contextmanager
def temporary_env_var(key, value):
    """
    A context manager for temporarily setting an environment variable
    with automatic cleanup after exiting the block, even in case of an error.
    """
    old_value = os.environ.get(key)

    os.environ[key] = value
    try:
        yield
    finally:
        del os.environ[key]

        if old_value is not None:
            os.environ[key] = old_value


T = TypeVar("T")


def lazy_var(compute: Callable[[], T]) -> Callable[[], T]:
    """
    A function that allows to create lazily-computed value.
    Useful for initialization of values that depend on
    global context (for example asyncio event loop) and
    cannot be initialized as plain global variables.
    """

    computed = False
    val = None

    def get_value():
        nonlocal computed, val
        if computed:
            return val
        else:
            val = compute()
            computed = True
            return val

    return get_value
