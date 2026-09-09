#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A relay must not outlive the switchboard process it was forked from.

Nothing takes a relay down when its parent dies: gunicorn signals only the
worker process, so the relay would carry on as an orphan while still holding
its port. A restarted switchboard cannot adopt a process it did not fork, so
the port could never be bound again and would stay unusable until somebody
killed the orphan by hand.

The parent is killed here rather than allowed to exit, because multiprocessing
joins its children on a clean exit - a hard kill is what actually happens when
gunicorn decides a worker is unresponsive.

Usage: test_relay_orphan.py [path-to-switchboard-dir]
"""

import os
import signal
import socket
import subprocess
import sys
import time

SWITCHBOARD_DIR = (sys.argv[1] if len(sys.argv) > 1
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = int(os.environ.get('TEST_PORT', 31996))

# starts a relay and then does nothing, so it can be killed while the relay runs
PARENT_SCRIPT = f"""
import logging, multiprocessing, sys, time
sys.path.insert(0, {SWITCHBOARD_DIR!r})
multiprocessing.set_start_method('fork', force=True)
import proxies
logging.basicConfig(level=logging.CRITICAL)
proxy = proxies.MirrorProxy(listen_port={PORT}, logger=logging.getLogger('orphan'))
proxy.start()
print(proxy.pid, flush=True)
time.sleep(600)
"""


def relays():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.5)
    try:
        sock.sendto(b'ping', ('127.0.0.1', PORT))
        return sock.recvfrom(64)[0] == b'ping'
    except socket.timeout:
        return False
    finally:
        sock.close()


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main():
    parent = subprocess.Popen([sys.executable, '-c', PARENT_SCRIPT],
            stdout=subprocess.PIPE, text=True,
            env={**os.environ, 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY': 'YES'})
    relay_pid = int(parent.stdout.readline().strip())
    time.sleep(0.5)
    checks = [('relay serves its port', relays())]

    # kill the parent outright, the way gunicorn kills an unresponsive worker
    parent.kill()
    parent.wait()
    checks.append(('parent is gone', not alive(parent.pid)))

    deadline = time.time() + 15
    while time.time() < deadline and alive(relay_pid):
        time.sleep(0.5)

    checks.append(('orphaned relay exits on its own', not alive(relay_pid)))
    checks.append(('its port is no longer served', not relays()))

    for name, ok in checks:
        print(f'  {"ok  " if ok else "FAIL"}  {name}')
    passed = all(ok for _name, ok in checks)
    if not passed and alive(relay_pid):
        os.kill(relay_pid, signal.SIGKILL)
    print(f'  RESULT: {"PASS" if passed else "FAIL"}')
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
