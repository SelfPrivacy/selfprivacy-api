#!/usr/bin/env python3
"""Various utility functions"""
import datetime
from enum import Enum
import json
import os
import subprocess
import portalocker


USERDATA_FILE = "/etc/nixos/userdata/userdata.json"
TOKENS_FILE = "/etc/nixos/userdata/tokens.json"
DOMAIN_FILE = "/var/domain"


class UserDataFiles(Enum):
    """Enum for userdata files"""

    USERDATA = 0
    TOKENS = 1


def get_domain():
    """Get domain from /var/domain without trailing new line"""
    with open(DOMAIN_FILE, "r", encoding="utf-8") as domain_file:
        domain = domain_file.readline().rstrip()
    return domain


class WriteUserData(object):
    """Write userdata.json with lock"""

    def __init__(self, file_type=UserDataFiles.USERDATA):
        if file_type == UserDataFiles.USERDATA:
            self.userdata_file = open(USERDATA_FILE, "r+", encoding="utf-8")
        elif file_type == UserDataFiles.TOKENS:
            self.userdata_file = open(TOKENS_FILE, "r+", encoding="utf-8")
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
        elif file_type == UserDataFiles.TOKENS:
            self.userdata_file = open(TOKENS_FILE, "r", encoding="utf-8")
        else:
            raise ValueError("Unknown file type")
        portalocker.lock(self.userdata_file, portalocker.LOCK_SH)
        self.data = json.load(self.userdata_file)

    def __enter__(self) -> dict:
        return self.data

    def __exit__(self, *args):
        portalocker.unlock(self.userdata_file)
        self.userdata_file.close()


def validate_ssh_public_key(key):
    """Validate SSH public key. It may be ssh-ed25519 or ssh-rsa."""
    if not key.startswith("ssh-ed25519"):
        if not key.startswith("ssh-rsa"):
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


def get_dkim_key(domain):
    """Get DKIM key from /var/dkim/<domain>.selector.txt"""
    if os.path.exists("/var/dkim/" + domain + ".selector.txt"):
        cat_process = subprocess.Popen(
            ["cat", "/var/dkim/" + domain + ".selector.txt"], stdout=subprocess.PIPE
        )
        dkim = cat_process.communicate()[0]
        return str(dkim, "utf-8")
    return None
