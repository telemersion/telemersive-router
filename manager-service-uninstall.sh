#!/bin/bash

### Uninstalls the manager as a service without it's dependencies.
### Florian Bruggisser 18.02.2021

# Read the asolute path to the script file.
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

pushd "$SCRIPT_PATH"

# load configuration
source manager-service.cfg

echo "stopping service..."
sudo systemctl stop $SERVICE_NAME.service

echo "disabling service..."
sudo systemctl disable $SERVICE_NAME.service

echo "cleaning up service files..."
sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"

echo "removing service user"
userdel $SERVICE_USER_NAME

echo "uninstall completed!"

popd