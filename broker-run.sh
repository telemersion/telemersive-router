#!/bin/bash

### This scripts starts the broker and can be used for testsing or deployment.
### The broker iteself is configured by relative pahts, so it's important that
### it runs inside the ./broker directory.
### Florian Bruggisser 16.02.2021

# Read the asolute path to the script file.
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo "Working Directory: $SCRIPT_PATH"

# switch to working directory
pushd "$SCRIPT_PATH/broker/"

# run mosquitto
mosquitto -c "mosquitto.conf"

popd