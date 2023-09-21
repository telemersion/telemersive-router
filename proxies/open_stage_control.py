#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
open_stage_control: runs an open stage control server on specified ports

For UDP transmission between OpenStageControl and many UDP clients to
work, the OSC server connects to a many2manyBi proxy that is assumed to
be already running on the port specified by the many_port parameter.
"""

import logging
import os
import subprocess
import signal
import sys

OSC_DEFAULT_SESSION_PATH = '/opt/open-stage-control/sessions/tsb_sessions'
#OSC_DEFAULT_SESSION_PATH = '/home/roman/pd-src/tsb_sessions'

# port: http port
# many-port: many2manyBi proxy


class OpenStageControl:
    """
    runs an Open Stage Control server. The idea is that each room in the TelemersiveBus runs
    one instance of this.
    """

    def __init__(self, http_port=None, many_port=None, session=None, logger=None):
        if not isinstance(http_port, int) or not  1024 <= http_port <= 65535:
            raise ValueError('Specified http_port "%s" is invalid.' % http_port)
        if not isinstance(many_port, int) or not  1024 <= many_port <= 65535:
            raise ValueError('Specified many_port "%s" is invalid.' % many_port)
        self.cmd = [
            '/usr/bin/node',
            '/usr/lib/open-stage-control/resources/app/',
            '--port',
            f'{http_port}',
            '--send',
            f'127.0.0.1:{many_port}',
            '--no-qrcode'
        ]
        self.session_name=session if session else 'default'

        self.logger = logger
        self.p = None

    def prepare_session_file(self):
        session_dir = f'{OSC_DEFAULT_SESSION_PATH}/{self.session_name}'
        self.session_path = f'{session_dir}/default.json'
        if not os.path.exists(session_dir):
            try:
                os.mkdir(session_dir)
            except OSError as error:
                self.logger.exception('Could not create session directory for '
                        'OpenStageControl:')
                self.logger.exception(error)
                self.session_path = None
                return
            default_session = f'{OSC_DEFAULT_SESSION_PATH}/template.json'
            try:
                os.system(f'cp {default_session} {self.session_path}')
            except OSError as error:
                self.logger.exception('Could not copy template to session '
                    'directory')
                self.logger.exception(error)
                self.session_path = None
                return

    def start(self):
        try:
            assert self.p is None
        except:
            self.logger.exception('This instance is already running', extra={'stack': True})
        self.prepare_session_file()
        if self.session_path:
            self.cmd.extend(['--load', self.session_path])
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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
