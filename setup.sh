#!/bin/bash

USER="tpf-switchboard"
APP_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
APP_NAME="switchboard"
SERVICE_NAME="tpf-switchboard"
LOG_DIR="/var/log/tpf-switchboard"
LISTEN_PORT=3591
LISTEN_ADDRESS="0.0.0.0"

function hilite {
  echo -ne "\033[32m"
  echo "${@}"
  echo -ne "\033[0m"
}

function errexit {
  echo -ne "\033[31m"
  echo "${@}"
  echo "Exiting prematurely."
  echo -ne "\033[0m"
  exit 1
}

# are we root?
hilite "Check whether we are root."
[ "$(whoami)" == "root" ] || errexit "We are not running as root. Exiting now." 

# Install flask
hilite "Make sure flask is installed"
if ! which flask > /dev/null
then
  apt-get install python3-flask || errexit "Failed to install python3-flask"
fi

# Install gunicorn3
hilite "Make sure gunicorn3 is installed"
if ! which gunicorn3 > /dev/null
then
  apt-get install gunicorn3 || errexit "Failed to install gunicorn3"
fi

# add user to the system
hilite "Add user '$USER' to the system"
if ! id -u "$USER" > /dev/null 2>&1
then
  useradd -r -s /usr/sbin/nologin $USER || errexit "Failed to add user '$USER'"
fi

# create log directory
hilite "Create log directory: '$LOG_DIR'"
mkdir -p "$LOG_DIR" || errexit "Could not create log directory"
chown -R ${USER}:${USER} "$LOG_DIR" || errexit "Could not change owenership of log directory"

SYSTEMD_UNIT_CONTENT="
[Unit]
Description=tpf-switchboard - manager for udp proxies
After=syslog.target

[Service]
Type=simple
ExecStart=/usr/bin/gunicorn3 \\
            --bind $LISTEN_ADDRESS:$LISTEN_PORT \\
            --chdir $APP_PATH \\
	    --graceful-timeout 1 \\
            --access-logfile /var/log/tpf-switchboard/access.log \\
            --error-logfile /var/log/tpf-switchboard/error.log \\
            $APP_NAME:app
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
"

hilite "Create service unit file: /etc/systemd/system/${SERVICE_NAME}.service"
echo "$SYSTEMD_UNIT_CONTENT" > /etc/systemd/system/${SERVICE_NAME}.service \
  || errexit "Could not create sytemd service unit file"

hilite "Enable and (re-)start service '$SERVICE_NAME'."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service || errexit "Failed ot enable service '$SERVICE_NAME'."
systemctl restart ${SERVICE_NAME}.service || errexit "Failed to start service '$SERVICE_NAME'."

hilite "Done. Exiting now."
exit 0
