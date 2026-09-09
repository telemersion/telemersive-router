#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The ordinary proxy lifecycle: start, relay, inspect, stop, start again.

Guards the everyday paths of the API against regressions from changes to proxy
teardown and socket handling - in particular that a stopped proxy really frees
its port, and that a proxy which is still alive is still refused.

Usage: test_proxy_lifecycle.py [path-to-switchboard-dir]
"""

import multiprocessing
import os
import socket
import sys
import time

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
multiprocessing.set_start_method('fork', force=True)

import switchboard

PORT = int(os.environ.get('TEST_PORT', 31993))
ROOM = 'lifecycleroom'
PAYLOAD = {'port': PORT, 'type': 'mirror', 'room': ROOM,
           'description': 'lifecycle test'}


def relays():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.sendto(b'ping', ('127.0.0.1', PORT))
        data, _addr = sock.recvfrom(1024)
        return data == b'ping'
    except socket.timeout:
        return False
    finally:
        sock.close()


def main():
    client = switchboard.app.test_client()
    checks = []

    started = client.post('/proxies/', json=PAYLOAD)
    checks.append(('start is accepted', started.status_code == 201))
    time.sleep(0.4)
    checks.append(('relays packets', relays()))

    listed = client.get('/proxies/')
    checks.append(('is listed', str(PORT) in listed.data.decode()))

    state = client.get(f'/proxies/{PORT}')
    checks.append(('state is readable', state.status_code == 200))

    room = client.get(f'/rooms/{ROOM}')
    checks.append(('is listed for its room', str(PORT) in room.data.decode()))

    duplicate = client.post('/proxies/', json=PAYLOAD)
    checks.append(('refused while still alive', duplicate.status_code == 422))

    stopped = client.delete(f'/proxies/{PORT}')
    checks.append(('stop is accepted', stopped.status_code == 200))
    checks.append(('is deregistered', PORT not in switchboard.myproxies))
    time.sleep(0.3)
    checks.append(('stops relaying', not relays()))

    restarted = client.post('/proxies/', json=PAYLOAD)
    checks.append(('port is free again', restarted.status_code == 201))
    time.sleep(0.4)
    checks.append(('relays again', relays()))
    client.delete(f'/proxies/{PORT}')

    for name, ok in checks:
        print(f'  {"ok  " if ok else "FAIL"}  {name}')
    passed = all(ok for _name, ok in checks)
    print(f'  RESULT: {"PASS" if passed else "FAIL"}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
