#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_one2manymo: for 1-to-N connections
"""

import socket
import sys
import threading
import time

class One2ManyMoProxy(threading.Thread):
    """
    Relays UDP packets from one source client to many sink clients. Sink clients
    are expected to send dummy packets in regular intervals to signal their presence.
    Different ports are used for source and sink clients.
    """

    def __init__(self, listen_port=None, send_port=None, listen_address='0.0.0.0', timeout=10):
        super(One2ManyMoProxy, self).__init__()
        for port in [listen_port, send_port]:
            if not isinstance(port, int) or not  1024 <= port <= 65535:
                raise ValueError('Specified port "%s" is invalid.' % port)
        try:
            self.source = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.source.settimeout(0.1)
            self.source.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        try:
            self.sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Make socket non-blocking by setting timeout to 0
            self.sink.settimeout(0)
            self.sink.bind((listen_address, send_port))
        except socket.error as msg:
            raise
        self.kill_signal = False
        # key of dict is sink_client's (address, port) tuple
        self.sink_clients = {}
        self.timeout = timeout

    def run(self):
        while not self.kill_signal:
            # handle incoming packets from sink clients
            while True:
                try:
                    _trash, sink_addr = self.sink.recvfrom(65536)
                except BlockingIOError:
                    break
                self.sink_clients[sink_addr] = time.time()

            # handle incoming packets from source client
            try:
                data, addr = self.source.recvfrom(65536)
            except socket.timeout:
                continue

            # remove expired clients from sink_clients
            for client, prev_ts in list(self.sink_clients.items()):
                if (prev_ts + self.timeout) < time.time():
                    del self.sink_clients[client]

            # send data to remaining sink_clients
            for client in self.sink_clients.keys():
                self.sink.sendto(data, client)

    def stop(self):
        self.kill_signal = True
        self.join()

def main():
    try:
        source_port = int(sys.argv[1])
        sink_port = source_port + 1
        proxy = One2ManyMoProxy(listen_port=source_port, send_port=sink_port)
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
