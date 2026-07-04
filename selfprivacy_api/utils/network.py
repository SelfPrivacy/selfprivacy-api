#!/usr/bin/env python3
"""Network utils"""

import ipaddress
import socket
from typing import Optional

import psutil


def get_ip4(interface: str = "eth0") -> str:
    """Get IPv4 address"""
    for addr in psutil.net_if_addrs().get(interface, []):
        if addr.family == socket.AF_INET:
            return addr.address
    return ""


def get_ip6(interface: str = "eth0") -> Optional[str]:
    """Get IPv6 address"""
    for addr in psutil.net_if_addrs().get(interface, []):
        if addr.family == socket.AF_INET6:
            address = addr.address.split("%", 1)[0]
            try:
                if ipaddress.IPv6Address(address).is_global:
                    return address
            except ipaddress.AddressValueError:
                continue
    return None
