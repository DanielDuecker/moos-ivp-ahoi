#!/bin/bash

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    SERIAL=$(sudo dmidecode -t system | grep 'Serial Number' | awk '{print $3}')
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    SERIAL=$(system_profiler SPHardwareDataType | grep "Serial Number" | awk '{print $4}')
else
    echo "Unsupported OS"
    exit 1
fi

# Output the serial number
echo "$SERIAL"