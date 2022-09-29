#!/bin/bash

### Installs the nat-helper as a systemd service.
### Roman Haefeli 29.09.2022 (based on scripts by Florian Bruggisser)

# Read the asolute path to the script file.
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

pushd "$SCRIPT_PATH"

# load configuration
source nat-helper-service.cfg

# add user
echo "adding service user..."
useradd -s /usr/sbin/nologin -r -M $SERVICE_USER_NAME

# grant access
setfacl -R -m u:$SERVICE_USER_NAME:rwx "$SCRIPT_PATH"

# prepare service configuration form template
echo "installing service..."
RUN_SCRIPT_PATH="$SCRIPT_PATH/nat-helper/nat-helper"
cp "nat-helper/$SERVICE_NAME.service.txt" "$SERVICE_NAME.service"

sed -i -e "s~%COMMAND%~$RUN_SCRIPT_PATH~g" "$SERVICE_NAME.service"
sed -i -e "s~%USER%~$SERVICE_USER_NAME~g" "$SERVICE_NAME.service"
sed -i -e "s~%PORT%~$SERVICE_PORT~g" "$SERVICE_NAME.service"

# install as service
sudo mv $SERVICE_NAME.service "/etc/systemd/system/$SERVICE_NAME.service"

echo "enabling service..."
sudo systemctl enable $SERVICE_NAME.service

echo ""
echo ""
echo "Please start your service now:"
echo "sudo systemctl start $SERVICE_NAME.service"
echo ""
echo ""

popd
