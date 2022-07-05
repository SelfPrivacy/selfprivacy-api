#!/usr/bin/env python3
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=missing-function-docstring
import pytest

from selfprivacy_api.utils.network import get_ip4, get_ip6

OUTPUT_STRING = b"""
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 96:00:00:f1:34:ae brd ff:ff:ff:ff:ff:ff
    altname enp0s3
    altname ens3
    inet 157.90.247.192/32 brd 157.90.247.192 scope global dynamic eth0
       valid_lft 46061sec preferred_lft 35261sec
    inet6 fe80::9400:ff:fef1:34ae/64 scope link
       valid_lft forever preferred_lft forever
"""

FAILED_OUTPUT_STRING = b"""
Device "eth0" does not exist.
"""

@pytest.fixture
def ip_process_mock(mocker):
    mock = mocker.patch("subprocess.check_output", autospec=True, return_value=OUTPUT_STRING)
    return mock

def test_get_ip4(ip_process_mock):
    """Test get IPv4 address"""
    ip4 = get_ip4()
    assert ip4 == "157.90.247.192"

def test_get_ip6(ip_process_mock):
    """Test get IPv6 address"""
    ip6 = get_ip6()
    assert ip6 == "fe80::9400:ff:fef1:34ae"
