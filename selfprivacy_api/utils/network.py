#!/usr/bin/env python3
"""Network utils"""
import subprocess
import re


def get_ip4():
    """Get IPv4 address"""
    try:
        ip4 = subprocess.check_output(["ip", "addr", "show", "dev", "eth0"]).decode(
            "utf-8"
        )
        ip4 = re.search(r"inet (\d+\.\d+\.\d+\.\d+)\/\d+", ip4)
    except subprocess.CalledProcessError:
        ip4 = None
    return ip4.group(1) if ip4 else None


def get_ip6():
    """Get IPv6 address"""
    try:
        ip6 = subprocess.check_output(["ip", "addr", "show", "dev", "eth0"]).decode(
            "utf-8"
        )
        ip6 = re.search(r"inet6 (\S+)\/\d+", ip6)
    except subprocess.CalledProcessError:
        ip6 = None
    return ip6.group(1) if ip6 else None
