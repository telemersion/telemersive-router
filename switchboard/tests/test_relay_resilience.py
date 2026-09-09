#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A relay must keep forwarding packets when the shared state manager dies.

All proxies of all rooms share one multiprocessing.Manager(), used only to
publish each relay's client list. That makes it a single point of failure
reaching every room at once: if a relay treated a failed state update as fatal,
losing the manager would silently kill every proxy on the host while the
telemersive-manager still reports all rooms as healthy.

Usage: test_relay_resilience.py [path-to-switchboard-dir]
"""

import logging
import multiprocessing
import os
import socket
import sys
import time

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import proxies

# the relays inherit their sockets and shared counters across the fork, so the
# forking start method is required (it is the default on linux)
multiprocessing.set_start_method('fork', force=True)

PORT = int(os.environ.get('TEST_PORT', 31991))
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger('test')


def roundtrip(sock, payload):
    sock.sendto(payload, ('127.0.0.1', PORT))
    try:
        data, _addr = sock.recvfrom(1024)
        return data
    except socket.timeout:
        return None


def main():
    manager = multiprocessing.Manager()
    # the logger is optional, so this also runs against an older checkout
    state = proxies.ProxyState(manager)
    proxy = proxies.MirrorProxy(listen_port=PORT, logger=logger, state=state)
    proxy.start()
    time.sleep(0.5)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    before = roundtrip(sock, b'before')
    print(f'  relays before manager dies : {before!r}')

    # take the shared state manager away from the running relay
    manager.shutdown()
    # the client list is synced at most once per SYNC_INTERVAL, so give the
    # relay a packet to handle and time to attempt a sync against a dead manager
    time.sleep(1.5)
    roundtrip(sock, b'trigger-sync')
    time.sleep(1.5)

    after = roundtrip(sock, b'after')
    alive = proxy.is_alive()
    print(f'  relays after manager dies  : {after!r}')
    print(f'  relay process still alive  : {alive}')

    sock.close()
    try:
        proxy.stop()
    except Exception:
        pass

    passed = before == b'before' and after == b'after' and alive
    print(f'  RESULT: {"PASS" if passed else "FAIL"}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
