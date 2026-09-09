#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
state: shared runtime state for a proxy, readable from the switchboard's
Flask process while the proxy itself runs in a separate process.
"""

import logging
import multiprocessing

COUNTER_NAMES = ('packets_in', 'bytes_in', 'packets_out', 'bytes_out')

# minimum time (in seconds) between two updates of the shared client list
SYNC_INTERVAL = 1

# how many relay loop iterations may fail in a row before a proxy gives up. a
# transient error must not kill a running proxy, but a permanently broken one
# should not spin forever either.
MAX_CONSECUTIVE_ERRORS = 10


def addr_key(addr):
    """Turn a (host, port) tuple into a 'host:port' string usable as a JSON key."""
    return f'{addr[0]}:{addr[1]}'


class ProxyState:
    """
    Counters use plain shared memory (cheap, single writer, no lock needed)
    while the client list uses a Manager dict that is synced at a low,
    throttled frequency to keep the impact on packet relaying minimal.

    The Manager dict is the one part of a proxy that depends on another
    process. Reporting through it is therefore treated as optional: if the
    manager process becomes unreachable, reporting is switched off and the
    proxy keeps relaying packets. Relaying itself needs nothing from it.
    """

    def __init__(self, manager, logger=None):
        self.clients = manager.dict()
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        # set once the manager process can no longer be reached from here.
        # after a fork each proxy carries its own copy, so one broken proxy
        # does not silence the others.
        self.reporting_disabled = False
        for name in COUNTER_NAMES:
            setattr(self, name, multiprocessing.Value('Q', 0, lock=False))

    def add(self, **counts):
        # plain shared memory, no other process involved - cannot fail on IPC
        for name, value in counts.items():
            counter = getattr(self, name)
            counter.value += value

    def disable_reporting(self, reason):
        if not self.reporting_disabled:
            self.reporting_disabled = True
            self.logger.warning('%s. Client list reporting is now disabled for '
                    'this proxy, packet relaying continues.', reason, exc_info=True)

    def set_clients(self, clients):
        if self.reporting_disabled:
            return
        try:
            self.clients.clear()
            self.clients.update(clients)
        except Exception:
            self.disable_reporting('Could not reach the shared state manager')

    def to_dict(self):
        d = {name: getattr(self, name).value for name in COUNTER_NAMES}
        try:
            d['clients'] = dict(self.clients)
        except Exception:
            # the api must keep answering even when the manager process is gone
            d['clients'] = {}
        return d
