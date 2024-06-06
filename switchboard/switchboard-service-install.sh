#!/bin/bash

# load configuration
source switchboard-service.cfg

USER=$SERVICE_USER_NAME
HOME="/opt/open-stage-control/sessions/tsb_sessions"
APP_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
APP_NAME="switchboard"
LOG_DIR="/var/log/telemersive-switchboard"
LISTEN_PORT=3591
LISTEN_ADDRESS="0.0.0.0"
DEB_PKGS="python3-flask gunicorn3 gdebi-core wget"
OSC_DEB="https://github.com/jean-emmanuel/open-stage-control/releases/download/v1.26.2/open-stage-control_1.26.2_amd64.deb"

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

# Install install stuff
hilite "Make sure deb packages are installed"
if ! which flask > /dev/null
then
  apt-get install -y $DEB_PKGS || errexit ""
fi


# add user to the system
hilite "Add user '$USER' to the system"
if ! id -u "$USER" > /dev/null 2>&1
then
  useradd -r -s /usr/sbin/nologin -d "$HOME" -m $USER || errexit "Failed to add user '$USER'"
fi

# prepare home
hilite "Prepare Home"
mkdir -p "${HOME}/.config" || errexit "Failed to create ~/.config for user"
chown -R ${USER}:${USER} "$HOME" || errexit " Failed change owner"

# create log directory
hilite "Create log directory: '$LOG_DIR'"
mkdir -p "$LOG_DIR" || errexit "Could not create log directory"
chown -R ${USER}:${USER} "$LOG_DIR" || errexit "Could not change owenership of log directory"

#  install open-stage-control
hilite "Install open-stage-control"
wget "$OSC_DEB" -O /tmp/openstagecontrol.deb || errexit "Couldn't download open-stage-control as deb package"
gdebi --n /tmp/openstagecontrol.deb  || errexit "Couldn't install open-stage-control from deb"
rm /tmp/openstagecontrol.deb || errexit "Couldn't remove /tmp/openstagecontrol.deb"

# install default session file (template.json)
hilite "Install default session for new rooms (template.json)"
cp files/template.json "$HOME" || errexit "Couln't copy template.json to ~/."
chown ${USER}:${USER} "${HOME}/template.json"  || errexit  "Couldn't  change owner for template.json"

SYSTEMD_UNIT_CONTENT="
[Unit]
Description=telemersive-switchboard - manager for udp proxies
After=syslog.target

[Service]
EnvironmentFile=$(readlink -f switchboard-service.cfg)
Type=simple
ExecStart=/usr/bin/gunicorn3 \\
            --bind \${SERVICE_LISTEN_ADDRESS}:\${SERVICE_LISTEN_PORT} \\
            --chdir $APP_PATH \\
	    --graceful-timeout 1 \\
            --access-logfile /var/log/telemersive-switchboard/access.log \\
            --error-logfile /var/log/telemersive-switchboard/error.log \\
            $APP_NAME:app
User=$USER
Group=$USER
KillMode=mixed
TimeoutStopSec=10s

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
