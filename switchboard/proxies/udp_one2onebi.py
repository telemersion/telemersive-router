#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_one2onebi: for 1-to-1 connections
"""

import logging
import multiprocessing
import socket
import sys


class One2OneBiProxy(multiprocessing.Process):
    """
    Relays UDP packets between two endpoints. This allows two end-points
    behind NAT firewalls to communicate with each other by relaying their traffic
    through a server with a public IP running this script.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0', logger=None):
        super(One2OneBiProxy, self).__init__()
        if not isinstance(listen_port, int) or not  1024 <= listen_port <= 65535:
            raise ValueError('Specified port "%s" is invalid.' % listen_port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.settimeout(0.1)
            self.sock.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        self.port = listen_port
        self.kill_signal = multiprocessing.Value('i', False)
        self.logger = logger

    def run(self):
        try:
            client1 = None
            client2 = None
            while not self.kill_signal.value:
                try:
                    data, addr = self.sock.recvfrom(65536)
                except socket.timeout:
                    continue

                # Assigning clients
                if addr != client1 and addr != client2:
                    client1 = client2
                    client2 = addr

                # transmit data
                if client1 and client2:
                    try:
                        if addr == client1:
                            self.sock.sendto(data, client2)
                        elif addr == client2:
                            self.sock.sendto(data, client1)
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
        proxy = One2OneBiProxy(listen_port=int(sys.argv[1]), logger=logger)
        proxy.start()
        proxy.join()
    except (KeyboardInterrupt, SystemExit):
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()

