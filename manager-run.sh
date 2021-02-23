#!/bin/bash

### This scripts starts the manager and can be used for testsing or deployment.
### The manager iteself is configured by relative pahts, so it's important that
### it runs inside the ./manager directory.
### Florian Bruggisser 18.02.2021

# Read the asolute path to the script file.
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo "Working Directory: $SCRIPT_PATH"

# switch to working directory
pushd "$SCRIPT_PATH/manager/"

# setup npm
npm install

# run bus manager
node busManager.js

popd
echo "manager closed"
