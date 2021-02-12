#!/bin/bash

USER="tpf-switchboard"
APP_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
APP_NAME="switchboard"
SERVICE_NAME="tpf-switchboard"
LISTEN_PORT=3591
LISTEN_ADDRESS="0.0.0.0"

# are we root?
if [ "$(whoami)" != "root" ]
then
  echo "We are not running as root. Exiting now."
  exit 1
fi

# Install flask
if ! which flask > /dev/null
then
  apt-get install python3-flask || exit 1
fi

# Install gunicorn3
if ! which gunicorn3 > /dev/null
then
  apt-get install gunicorn3 || exit 1
fi

# add user to the system
if ! id -u "$USER" > /dev/null 2>&1
then
  useradd -r -s /usr/sbin/nologin $USER || exit 1
fi

SYSTEMD_UNIT_CONTENT="
[Unit]
Description=tpf-switchboard - manager for udp proxies
After=syslog.target

[Service]
Type=simple
ExecStart=/usr/bin/gunicorn3 \\
            --bind $LISTEN_ADDRESS:$LISTEN_PORT \\
	    --chdir $APP_PATH \\
	    $APP_NAME:app
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
"

echo "$SYSTEMD_UNIT_CONTENT" > /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service
