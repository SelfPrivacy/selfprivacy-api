#!/usr/bin/env python3
"""Network utils"""
import subprocess
import re
import ipaddress
from typing import Optional


def get_ip4() -> str:
    """Get IPv4 address"""
    try:
        ip4 = subprocess.check_output(["ip", "addr", "show", "dev", "eth0"]).decode(
            "utf-8"
        )
        ip4 = re.search(r"inet (\d+\.\d+\.\d+\.\d+)\/\d+", ip4)
    except subprocess.CalledProcessError:
        ip4 = None
    return ip4.group(1) if ip4 else ""


def get_ip6() -> Optional[str]:
    """Get IPv6 address"""
    try:
        ip6_addresses = subprocess.check_output(
            ["ip", "addr", "show", "dev", "eth0"]
        ).decode("utf-8", "replace")
        ip6_addresses = re.findall(r"inet6 (\S+)\/\d+", ip6_addresses)
        for address in ip6_addresses:
            if ipaddress.IPv6Address(address).is_global:
                return address
    except subprocess.CalledProcessError:
        return None
