#!/bin/bash

# Call get_modem_id.sh to retrieve the CPU serial number

SERIAL=$(get_cpu_serial.sh)

# Define the lookup table as an associative array

# Use a case statement to match the CPU serial number to a modem ID
case "$SERIAL" in
    # Ray's macbook
    "D9QC6H97PM")
        MODEM_ID="-1"
        ;;
    "CPU_SERIAL_2")
        MODEM_ID="0"
        ;;
    "CPU_SERIAL_3")
        MODEM_ID="2"
        ;;
    "CPU_SERIAL_4")
        MODEM_ID="5"
        ;;
    "CPU_SERIAL_5")
        MODEM_ID="7"
        ;;
    *)
        # Default case for unknown serial numbers
        MODEM_ID="-1"
        ;;
esac

# Lookup the modem ID based on the CPU serial number
# Check if the modem ID was found, and output the result
if [[ -n "$MODEM_ID" ]]; then
    echo $MODEM_ID
else
    # Not an enrolled ID, may be in simulation
    echo "-1"
fi