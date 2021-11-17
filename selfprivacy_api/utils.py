#!/usr/bin/env python3
"""Various utility functions"""


def get_domain():
    """Get domain from /var/domain without trailing new line"""
    with open("/var/domain", "r", encoding="utf-8") as domain_file:
        domain = domain_file.readline().rstrip()
    return domain
