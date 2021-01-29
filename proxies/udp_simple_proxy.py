#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_simple_proxy: for 1-to-1 connections
"""

import socket
import sys
import threading
import time

class SimpleProxy(threading.Thread):
    """
    Relays UDP packets between two endpoints. This allows two end-points
    behind NAT firewalls to communicate with each other by relaying their traffic
    through a server with a public IP running this script.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0'):
        super(SimpleProxy, self).__init__()
        if not isinstance(listen_port, int) or not  1024 <= listen_port <= 65535:
            raise ValueError('Specified port "%s" is invalid.' % listen_port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.1)
            self.sock.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        self.kill_signal = False

    def run(self):
        client1 = None
        client2 = None
        while not self.kill_signal:
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
                if addr == client1:
                    self.sock.sendto(data, client2)
                elif addr == client2:
                    self.sock.sendto(data, client1)

    def stop(self):
        self.kill_signal = True
        self.join()


def main():
    try:
        proxy = SimpleProxy(listen_port=int(sys.argv[1]))
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()

