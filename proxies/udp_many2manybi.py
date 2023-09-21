#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_many2manybi: for N-to-N connections (OSC)
"""

import logging
import multiprocessing
import socket
import sys
import time

class Many2ManyBiProxy(multiprocessing.Process):
    """
    Relays UDP packets between many endpoints. Incoming packets are forwarded
    to all other endpoints (not to itself). The OSC messages '/hb' is not
    forwarded, but keeps connection alive.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0', timeout=10, logger=None):
        super(Many2ManyBiProxy, self).__init__()
        if not isinstance(listen_port, int) or not  1024 <= listen_port <= 65535:
            raise ValueError('Specified port "%s" is invalid.' % listen_port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(0.1)
            self.sock.bind((listen_address, listen_port))
            self.port = listen_port
        except socket.error as msg:
            raise
        self.kill_signal = multiprocessing.Value('i', False)
        # key of dict is client's (address, port) tuple
        self.active_endpoints = {}
        self.timeout = timeout
        self.logger = logger
        self.heartbeat_sequence = bytes([47, 104, 98, 0, 44, 0, 0, 0])

    def run(self):
        try:
            while not self.kill_signal.value:
                try:
                    my_data, my_addr = self.sock.recvfrom(65536)
                except socket.timeout:
                    continue
                self.active_endpoints[my_addr] = time.time()
                if self.heartbeat_sequence != my_data[:len(self.heartbeat_sequence)]:
                    other_clients = list(self.active_endpoints.keys())
                    other_clients.remove(my_addr)
                    for addr in other_clients:
                        if ((addr[0] != '127.0.0.1') and
                            (self.active_endpoints[addr] + self.timeout)) < time.time():
                            del self.active_endpoints[addr]
                        else:
                            try:
                                self.sock.sendto(my_data, addr)
                            except BlockingIOError:
                                continue
        except (KeyboardInterrupt, SystemExit):
            self.logger.warning(f'Shutting down proxy on {self.port}')
        except:
            self.logger.exception('Oops, something went wrong!', extra={'stack': True})
        self.sock.close()

    def stop(self):
        self.kill_signal.value = True
        self.join()

def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    try:
        listen_port = int(sys.argv[1])
        proxy = Many2ManyBiProxy(listen_port=listen_port, logger=logger)
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
