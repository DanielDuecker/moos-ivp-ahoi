#!/bin/bash

#pAntler ahoi_modem_static.moos --> start this seperately =/

# Get the directory of the bash script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the arguments relative to the script directory
SERVER_HOST="localhost"
SERVER_PORT="9000"
MODEM_CONFIG_FILE="$SCRIPT_DIR/local_modem_config.json"
ENVIRO_CONFIG_FILE="$SCRIPT_DIR/enviro_config.json"

# Define the path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/../../src/pAhoiModemManager/pyAhoi_MobileBase_Manager.py"

# Run the Python script with the arguments
python3 "$PYTHON_SCRIPT" --server_host $SERVER_HOST --server_port $SERVER_PORT --modem_config_file $MODEM_CONFIG_FILE --enviro_config_file $ENVIRO_CONFIG_FILE
