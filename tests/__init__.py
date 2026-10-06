"""Test package. Tests must never reach the network: any connection to a
non-loopback host fails immediately, so a test cannot accidentally call Qloo."""

import os
import socket

# A proxy listens on loopback, so blocking remote hosts alone is not enough:
# drop proxy settings for the whole test run.
for _name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
    os.environ.pop(_name, None)

_LOOPBACK = {"localhost", "127.0.0.1", "::1"}
_real_create_connection = socket.create_connection
_real_connect = socket.socket.connect


def _host_of(address):
    return address[0] if isinstance(address, tuple) else address


def _guarded_create_connection(address, *args, **kwargs):
    if _host_of(address) not in _LOOPBACK:
        raise ConnectionRefusedError(f"tests may not reach the network ({_host_of(address)})")
    return _real_create_connection(address, *args, **kwargs)


def _guarded_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and _host_of(address) not in _LOOPBACK:
        raise ConnectionRefusedError(f"tests may not reach the network ({_host_of(address)})")
    return _real_connect(self, address)


socket.create_connection = _guarded_create_connection
socket.socket.connect = _guarded_connect
