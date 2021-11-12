#!/usr/bin/env python3

# Get domain from /var/domain without trailing new line
def get_domain():
    with open("/var/domain", "r") as f:
        domain = f.readline().rstrip()
    return domain
