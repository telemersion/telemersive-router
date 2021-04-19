#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
udp_mirror: reflects udp packets to their origin
"""

import logging
import multiprocessing
import socket
import sys


class MirrorProxy(multiprocessing.Process):
    """
    Relays any incoming UDP packets back to the sender. Mainly useful for testing
    purposes.
    """

    def __init__(self, listen_port=None, listen_address='0.0.0.0', logger=None):
        super(MirrorProxy, self).__init__()
        if not isinstance(listen_port, int) or not  1024 <= listen_port <= 65535:
            raise ValueError('Specified port "%s" is invalid.' % listen_port)
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.1)
            self.sock.bind((listen_address, listen_port))
        except socket.error as msg:
            raise
        self.kill_signal = multiprocessing.Value('i', False)
        self.logger = logger

    def run(self):
        while not self.kill_signal.value:
            try:
                try:
                    data, addr = self.sock.recvfrom(65536)
                except socket.timeout:
                    continue
                self.sock.sendto(data, addr)
            except:
                self.logger.exception('Oops, something went wrong!', extra={'stack': True})

    def stop(self):
        self.kill_signal.value = True
        self.join()

def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    try:
        proxy = MirrorProxy(listen_port=int(sys.argv[1]), logger=logger)
        proxy.start()
        proxy.terminate()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
