#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
state: shared runtime state for a proxy, readable from the switchboard's
Flask process while the proxy itself runs in a separate process.
"""

import multiprocessing

COUNTER_NAMES = ('packets_in', 'bytes_in', 'packets_out', 'bytes_out')

# minimum time (in seconds) between two updates of the shared client list
SYNC_INTERVAL = 1


def addr_key(addr):
    """Turn a (host, port) tuple into a 'host:port' string usable as a JSON key."""
    return f'{addr[0]}:{addr[1]}'


class ProxyState:
    """
    Counters use plain shared memory (cheap, single writer, no lock needed)
    while the client list uses a Manager dict that is synced at a low,
    throttled frequency to keep the impact on packet relaying minimal.
    """

    def __init__(self, manager):
        self.clients = manager.dict()
        for name in COUNTER_NAMES:
            setattr(self, name, multiprocessing.Value('Q', 0, lock=False))

    def add(self, **counts):
        for name, value in counts.items():
            counter = getattr(self, name)
            counter.value += value

    def set_clients(self, clients):
        self.clients.clear()
        self.clients.update(clients)

    def to_dict(self):
        d = {name: getattr(self, name).value for name in COUNTER_NAMES}
        d['clients'] = dict(self.clients)
        return d
