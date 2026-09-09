#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The supervisor brings a dead relay back without anyone asking it to.

Nothing else in the system notices that a relay has died. The
telemersive-manager tracks peer liveness over MQTT rather than the media path,
and it only creates ports for a room that does not exist yet, so a room that
outlives its proxies would keep its ports dead until every peer has left it.

Also checks that a port which cannot be kept alive is eventually left alone
instead of being restarted forever.

Usage: test_proxy_supervisor.py [path-to-switchboard-dir]
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

PORT = int(os.environ.get('TEST_PORT', 31994))
PAYLOAD = {'port': PORT, 'type': 'mirror', 'room': 'supervisedroom',
           'description': 'supervisor test'}


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


def kill_relay():
    obj = switchboard.myproxies[PORT]['obj']
    obj.terminate()
    for _attempt in range(50):
        if not obj.is_alive():
            return True
        time.sleep(0.1)
    return False


def main():
    client = switchboard.app.test_client()
    checks = []

    started = client.post('/proxies/', json=PAYLOAD)
    if started.status_code != 201:
        print('  RESULT: FAIL (could not start a proxy at all)')
        return 1
    time.sleep(0.4)
    checks.append(('relays before being killed', relays()))

    checks.append(('relay killed', kill_relay()))
    checks.append(('stops relaying while dead', not relays()))

    # the supervisor runs on a timer in the service; drive one pass directly so
    # the test does not have to wait for it
    revived = switchboard.revive_dead_proxies()
    checks.append(('supervisor reports the port revived', revived == [PORT]))
    time.sleep(0.4)
    checks.append(('relays again without being asked', relays()))
    checks.append(('still registered for its room',
            switchboard.myproxies.get(PORT, {}).get('room') == 'supervisedroom'))

    state = client.get(f'/proxies/{PORT}/state')
    checks.append(('state reports the revival',
            b'"revivals": 1' in state.data or b'"revivals":1' in state.data))

    # a port that cannot be kept alive must not be restarted forever
    for _attempt in range(switchboard.max_proxy_revivals + 2):
        kill_relay()
        switchboard.revive_dead_proxies()
    checks.append(('gives up after the revival limit',
            switchboard.myproxies[PORT]['revivals'] <= switchboard.max_proxy_revivals))
    checks.append(('a dead proxy at the limit stays registered',
            PORT in switchboard.myproxies))

    client.delete(f'/proxies/{PORT}')

    for name, ok in checks:
        print(f'  {"ok  " if ok else "FAIL"}  {name}')
    passed = all(ok for _name, ok in checks)
    print(f'  RESULT: {"PASS" if passed else "FAIL"}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
