#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_mirror: reflects udp packets to their origin
"""

import socket
import sys
import threading
import time

class Mirror(threading.Thread):
    """
    Relays any incoming UDP packets back to the sender. Mainly useful for testing
    purposes.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0'):
        super(Mirror, self).__init__()
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
        while not self.kill_signal:
            try:
                data, addr = self.sock.recvfrom(65536)
            except socket.timeout:
                continue
            self.sock.sendto(data, addr)

    def stop(self):
        self.kill_signal = True
        self.join()

def main():
    try:
        proxy = Mirror(listen_port=int(sys.argv[1]))
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
