#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A port whose relay has died must be reusable.

An entry in myproxies records that a proxy was started once, not that it is
still running. If a dead entry kept answering 'Proxy already running' for its
own port, that port could only be revived by tearing down the whole room, which
requires every peer to leave first - impossible during a session. The proxy's
socket is opened in the switchboard process too, so it also has to be closed
here or the port stays bound after the relay is gone.

Usage: test_proxy_recovery.py [path-to-switchboard-dir]
"""

import multiprocessing
import os
import sys
import time

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
multiprocessing.set_start_method('fork', force=True)

import switchboard

PORT = int(os.environ.get('TEST_PORT', 31992))
PAYLOAD = {'port': PORT, 'type': 'mirror', 'room': 'recoveryroom',
           'description': 'recovery test'}


def main():
    client = switchboard.app.test_client()

    started = client.post('/proxies/', json=PAYLOAD)
    print(f'  initial start                 : {started.status_code}')
    if started.status_code != 201:
        print('  RESULT: FAIL (could not start a proxy at all)')
        return 1

    # kill the relay behind the switchboard's back, the way a crash would
    obj = switchboard.myproxies[PORT]['obj']
    obj.terminate()
    for _attempt in range(50):
        if not obj.is_alive():
            break
        time.sleep(0.1)
    print(f'  relay killed, still alive     : {obj.is_alive()}')
    print(f'  still registered in myproxies : {PORT in switchboard.myproxies}')

    restarted = client.post('/proxies/', json=PAYLOAD)
    print(f'  restart on the same port      : {restarted.status_code} '
            f'{restarted.data.decode().strip()}')

    passed = (restarted.status_code == 201
            and PORT in switchboard.myproxies
            and switchboard.myproxies[PORT]['obj'].is_alive())
    print(f'  port is serving again         : {passed}')

    client.delete(f'/proxies/{PORT}')
    print(f'  RESULT: {"PASS" if passed else "FAIL"}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
