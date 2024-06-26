#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_one2manybi: for 1-to-N connections (both directions)
"""

import logging
import multiprocessing
import select
import socket
import sys
import time

class One2ManyBiProxy(multiprocessing.Process):
    """
    Relays UDP packets from one source client to many sink clients. Sink clients
    are expected to send dummy packets in regular intervals to signal their presence.
    Different ports are used for source and sink clients.
    """

    def __init__(self, listen_port=None, many_port=None, listen_address='0.0.0.0', timeout=10, logger=None):
        super(One2ManyBiProxy, self).__init__()
        for port in [listen_port, many_port]:
            if not isinstance(port, int) or not  1024 <= port <= 65535:
                raise ValueError('Specified port "%s" is invalid.' % port)
        try:
            self.source = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.source.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.source.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        try:
            self.sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sink.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sink.bind((listen_address, many_port))
        except socket.error as msg:
            raise
        self.kill_signal = multiprocessing.Value('i', False)
        self.logger = logger
        # key of dict is sink_client's (address, port) tuple
        self.active_endpoints = {}
        self.timeout = timeout
        self.heartbeat_sequence = bytes([47, 104, 98, 0, 44, 0, 0, 0])
        self.listen_port = listen_port
        self.many_port = many_port

    def run(self):
        try:
            listening_sockets = [self.source, self.sink]
            while not self.kill_signal.value:
                readables, _w, _x = select.select(listening_sockets, [], [], 0.1)
                for sock in readables:
                    if sock.getsockname()[1] == self.many_port:
                        # many sends back to one
                        many_data, many_addr = sock.recvfrom(65536)
                        self.active_endpoints[many_addr] = time.time()
                        if self.heartbeat_sequence != many_data[:len(self.heartbeat_sequence)]:
                            try:
                                self.active_endpoints[one_addr]
                            except KeyError:
                                # Do nothing after ithe 'one' endpoint has expired
                                continue
                            except UnboundLocalError:
                                continue
                            if (self.active_endpoints[one_addr] + self.timeout) < time.time():
                                del self.active_endpoints[one_addr]
                            else:
                                try:
                                    self.source.sendto(many_data, one_addr)
                                except BlockingIOError:
                                    continue
                    elif sock.getsockname()[1] == self.listen_port:
                        # one sends to many
                        one_data, one_addr = sock.recvfrom(65536)
                        self.active_endpoints[one_addr] = time.time()
                        if self.heartbeat_sequence != one_data[:len(self.heartbeat_sequence)]:
                            many_list = list(self.active_endpoints.keys())
                            many_list.remove(one_addr)
                            for many_addr in many_list:
                                if (self.active_endpoints[many_addr] + self.timeout) < time.time():
                                    del self.active_endpoints[many_addr]
                                else:
                                    try:
                                        self.sink.sendto(one_data, many_addr)
                                    except BlockingIOError:
                                        continue
                    else:
                        print('We should not ever reach that point')
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
        listen_port = int(sys.argv[1])
        try:
            many_port = int(sys.argv[2])
        except IndexError:
            many_port = listen_port + 1
        proxy = One2ManyBiProxy(listen_port=listen_port, many_port=many_port, logger=logger)
        proxy.start()
        proxy.join()
    except (KeyboardInterrupt, SystemExit):
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
