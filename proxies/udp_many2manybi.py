#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_many2manybi: for N-to-N connections (OSC)
"""

import socket
import sys
import threading
import time

class Many2ManyBiProxy(threading.Thread):
    """
    Relays UDP packets between many endpoints. Incoming packets are forwarded to all other
    endpoints (not to itself). OSC messages '/hb' are not forwarded, but keep connection
    alive.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0', timeout=10):
        super(Many2ManyBiProxy, self).__init__()
        if not isinstance(listen_port, int) or not  1024 <= listen_port <= 65535:
            raise ValueError('Specified port "%s" is invalid.' % port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.1)
            self.sock.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        self.kill_signal = False
        # key of dict is client's (address, port) tuple
        self.active_endpoints = {}
        self.timeout = timeout
        self.heartbeat_sequence = bytes([47, 104, 98, 0, 44, 0, 0, 0])

    def run(self):
        while not self.kill_signal:
            try:
                my_data, my_addr = self.sock.recvfrom(65536)
            except socket.timeout:
                continue
            self.active_endpoints[my_addr] = time.time()
            if self.heartbeat_sequence != my_data[:len(self.heartbeat_sequence)]:
                for addr in self.active_endpoints.keys():
                    if addr != my_addr:
                        if (self.active_endpoints[addr] + self.timeout) < time.time():
                            del self.active_endpoints[addr]
                        else:
                            self.sock.sendto(my_data, addr)

    def stop(self):
        self.kill_signal = True
        self.join()

def main():
    try:
        listen_port = int(sys.argv[1])
        proxy = Many2ManyBiProxy(listen_port=listen_port)
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
