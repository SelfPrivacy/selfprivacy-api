#!/usr/bin/env python3
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import socket
from collections import namedtuple

import pytest

from selfprivacy_api.utils.network import get_ip4, get_ip6

# Mirrors the shape of psutil._common.snicaddr without depending on psutil
# being importable on the host (it only ships inside the Nix dev shell).
snicaddr = namedtuple("snicaddr", ["family", "address", "netmask", "broadcast", "ptp"])

NET_IF_ADDRS = {
    "eth0": [
        snicaddr(
            family=socket.AF_INET,
            address="157.90.247.192",
            netmask="255.255.255.255",
            broadcast="157.90.247.192",
            ptp=None,
        ),
        snicaddr(
            family=socket.AF_INET6,
            address="fe80::9400:ff:fef1:34ae%eth0",
            netmask="ffff:ffff:ffff:ffff::",
            broadcast=None,
            ptp=None,
        ),
        snicaddr(
            family=socket.AF_INET6,
            address="2a01:4f8:c17:7e3d::2",
            netmask="ffff:ffff:ffff:ffff::",
            broadcast=None,
            ptp=None,
        ),
    ]
}

NET_IF_ADDRS_WITHOUT_IP6 = {
    "eth0": [
        snicaddr(
            family=socket.AF_INET,
            address="157.90.247.192",
            netmask="255.255.255.255",
            broadcast="157.90.247.192",
            ptp=None,
        ),
        snicaddr(
            family=socket.AF_INET6,
            address="fe80::9400:ff:fef1:34ae%eth0",
            netmask="ffff:ffff:ffff:ffff::",
            broadcast=None,
            ptp=None,
        ),
    ]
}

NET_IF_ADDRS_MALFORMED_IP6 = {
    "eth0": [
        snicaddr(
            family=socket.AF_INET6,
            address="not-an-ip",
            netmask=None,
            broadcast=None,
            ptp=None,
        ),
        snicaddr(
            family=socket.AF_INET6,
            address="2a01:4f8:c17:7e3d::2",
            netmask="ffff:ffff:ffff:ffff::",
            broadcast=None,
            ptp=None,
        ),
    ]
}


@pytest.fixture
def net_if_addrs_mock(mocker):
    return mocker.patch(
        "selfprivacy_api.utils.network.psutil.net_if_addrs",
        autospec=True,
        return_value=NET_IF_ADDRS,
    )


@pytest.fixture
def net_if_addrs_mock_without_ip6(mocker):
    return mocker.patch(
        "selfprivacy_api.utils.network.psutil.net_if_addrs",
        autospec=True,
        return_value=NET_IF_ADDRS_WITHOUT_IP6,
    )


@pytest.fixture
def net_if_addrs_mock_missing_interface(mocker):
    return mocker.patch(
        "selfprivacy_api.utils.network.psutil.net_if_addrs",
        autospec=True,
        return_value={},
    )


@pytest.fixture
def net_if_addrs_mock_malformed_ip6(mocker):
    return mocker.patch(
        "selfprivacy_api.utils.network.psutil.net_if_addrs",
        autospec=True,
        return_value=NET_IF_ADDRS_MALFORMED_IP6,
    )


def test_get_ip4(net_if_addrs_mock):
    """Test get IPv4 address"""
    ip4 = get_ip4()
    assert ip4 == "157.90.247.192"


def test_get_ip6(net_if_addrs_mock):
    """Test get IPv6 address"""
    ip6 = get_ip6()
    assert ip6 == "2a01:4f8:c17:7e3d::2"


def test_get_ip4_custom_interface(net_if_addrs_mock):
    ip4 = get_ip4(interface="wlan0")
    assert ip4 == ""


def test_get_ip6_custom_interface(net_if_addrs_mock):
    ip6 = get_ip6(interface="wlan0")
    assert ip6 is None


def test_failed_get_ip4_missing_interface(net_if_addrs_mock_missing_interface):
    ip4 = get_ip4()
    assert ip4 == ""


def test_failed_get_ip6_missing_interface(net_if_addrs_mock_missing_interface):
    ip6 = get_ip6()
    assert ip6 is None


def test_failed_get_ip6_when_only_link_local(net_if_addrs_mock_without_ip6):
    ip6 = get_ip6()
    assert ip6 is None


def test_get_ip6_skips_malformed_address(net_if_addrs_mock_malformed_ip6):
    ip6 = get_ip6()
    assert ip6 == "2a01:4f8:c17:7e3d::2"
