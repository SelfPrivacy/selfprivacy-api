#!/usr/bin/env python3
"""Various utility functions"""
import json
import portalocker


def get_domain():
    """Get domain from /var/domain without trailing new line"""
    with open("/var/domain", "r", encoding="utf-8") as domain_file:
        domain = domain_file.readline().rstrip()
    return domain


class WriteUserData(object):
    """Write userdata.json with lock"""

    def __init__(self):
        self.userdata_file = open(
            "/etc/nixos/userdata/userdata.json", "r+", encoding="utf-8"
        )
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

    def __init__(self):
        self.userdata_file = open(
            "/etc/nixos/userdata/userdata.json", "r", encoding="utf-8"
        )
        portalocker.lock(self.userdata_file, portalocker.LOCK_SH)
        self.data = json.load(self.userdata_file)

    def __enter__(self):
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
    