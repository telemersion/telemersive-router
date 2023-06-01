#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
open_stage_control: runs an open stage control server on specified ports
"""

import logging
import subprocess
import signal
import sys


class OpenStageControl:
    """
    runs an Open Stage Control server. The idea is that each room in the TelemersiveBus runs
    one instance of this.
    """

    def __init__(self, http_port=None, osc_port=None, listen_address='0.0.0.0', logger=None):
        if not isinstance(http_port, int) or not  1024 <= http_port <= 65535:
            raise ValueError('Specified http_port "%s" is invalid.' % http_port)
        if not isinstance(osc_port, int) or not  1024 <= osc_port <= 65535:
            raise ValueError('Specified osc_port "%s" is invalid.' % osc_port)
        self.cmd = f"/usr/bin/node /usr/lib/open-stage-control/resources/app/ --port {http_port} --osc-port {osc_port} --no-qrcode"
        self.logger = logger
        self.p = None

    def start(self):
        try:
            assert self.p is None
        except:
            self.logger.exception('This instance is already running', extra={'stack': True})
        self.p = subprocess.Popen(self.cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def stop(self):
        if isinstance(self.p, subprocess.Popen):
            self.p.send_signal(signal.SIGINT)
            self.logger.info(self.p.communicate())
            self.p = None

    def join(self):
        if isinstance(self.p, subprocess.Popen):
            self.p.wait()
            self.logger.info(self.p.communicate())

    def terminate(self):
        return

def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(handler)
    try:
        proxy = OpenStageControl(http_port=int(sys.argv[1]), osc_port=int(sys.argv[2]), logger=logger)
        proxy.start()
        proxy.join()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)

if __name__ == '__main__':
        main()
