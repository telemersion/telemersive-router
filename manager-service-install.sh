#!/bin/bash

### Installs the manager as a service and all its dependencies.
### Florian Bruggisser 18.02.2021

# Read the asolute path to the script file.
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

pushd "$SCRIPT_PATH"

# load configuration
source manager-service.cfg

# install prerequisites if necessary (only on Linux)
echo "installing msoquitto..."
sudo apt update
sudo apt install acl -y

# installing node
curl -fsSL https://deb.nodesource.com/setup_15.x | bash -
sudo apt-get install -y nodejs
sudo apt-get install gcc g++ make

# add user
echo "adding service user..."
useradd -s /usr/sbin/nologin -r -M $SERVICE_USER_NAME

# grant access
setfacl -R -m u:$SERVICE_USER_NAME:rwx "$SCRIPT_PATH"

# install node packages
npm install

# prepare service configuration form template
echo "installing service..."
RUN_SCRIPT_PATH="$SCRIPT_PATH/broker-run.sh"
cp "manager/$SERVICE_NAME.service.txt" "$SERVICE_NAME.service"

sed -i -e "s~%COMMAND%~$RUN_SCRIPT_PATH~g" "$SERVICE_NAME.service"
sed -i -e "s~%USER%~$SERVICE_USER_NAME~g" "$SERVICE_NAME.service"

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
