#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_one2manymo: for 1-to-N connections
"""

import logging
import multiprocessing
import socket
import sys
import time

class One2ManyMoProxy(multiprocessing.Process):
    """
    Relays UDP packets from one source client to many sink clients. Sink clients
    are expected to send dummy packets in regular intervals to signal their presence.
    Different ports are used for source and sink clients.
    """

    def __init__(self, listen_port=None, many_port=None, listen_address='0.0.0.0', timeout=10, logger=None):
        super(One2ManyMoProxy, self).__init__()
        for port in [listen_port, many_port]:
            if not isinstance(port, int) or not  1024 <= port <= 65535:
                raise ValueError('Specified port "%s" is invalid.' % port)
        try:
            self.source = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.source.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.source.settimeout(0.1)
            self.source.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        try:
            self.sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sink.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Make socket non-blocking by setting timeout to 0
            self.sink.settimeout(0)
            self.sink.bind((listen_address, many_port))
        except socket.error as msg:
            raise
        self.kill_signal = multiprocessing.Value('i', False)
        self.logger = logger
        # key of dict is sink_client's (address, port) tuple
        self.sink_clients = {}
        self.timeout = timeout
        self.listen_port = listen_port

    def run(self):
        try:
            while not self.kill_signal.value:
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
                    try:
                        self.sink.sendto(data, client)
                    except BlockingIOError:
                        continue
        except (KeyboardInterrupt, SystemExit):
            self.logger.warning(f'Shutting down proxy on {self.listen_port}')
        except:
            self.logger.exception('Oops, something went wrong!', extra={'stack': True})
        self.source.close()
        self.sink.close()

    def stop(self):
        self.kill_signal.value = True
        self.join()

def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    try:
        source_port = int(sys.argv[1])
        try:
            sink_port = int(sys.argv[2])
        except IndexError:
            sink_port = source_port + 1
        proxy = One2ManyMoProxy(listen_port=source_port, many_port=sink_port, logger=logger)
        proxy.start()
        proxy.join()
    except (KeyboardInterrupt, SystemExit):
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
