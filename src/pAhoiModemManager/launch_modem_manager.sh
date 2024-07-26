!/bin/bash

# FUNCTIONALITY: driver dependency, log file folder creation, log file management (& deletion),  run program

# Initialize the variable "is_created" to 0, used for directory handle
# is_created=0

# Check if nucleus_driver is installed; if not, install it
# if ! pip3 show nucleus_driver > /dev/null 2>&1; then
#   echo "nucleus_driver is not installed. Installing..."
#   pip3 install nucleus_driver
# fi

# Check if "logs" subdirectory exists; if not, create it
# if [ ! -d "logs" ]; then
#   echo "Creating 'logs' subdirectory..."
#   mkdir logs
#   is_created=1  # Update the "is_created" variable to 1
# fi

# Initialize the variable "logfile_keep" for how many (most recent) log files to keep at once
# logfile_keep=5
# # decrement by one because removes logs before present run added
# logfile_keep=$((logfile_keep - 1))  

# Function to sort directories by their timestamps (recency)
# sort_dirs_by_timestamp() {
#   ls -1 -r -d logs/*/ | sort -t_ -k1.1n -k1.3n -k1.5n -k1.7n -k2.1n -k2.3n -k2.5n
# }

# Initialize variables for log directories and number of directories
# log_dirs=()
# num_dirs=0
# 
# Check if the "logs" directory has been created and is not empty
# if [ "$is_created" -ne 1 ] && [ -n "$(ls -A logs)" ]; then
#   # Get a list of all log directories sorted by timestamp (recency)
#   log_dirs=($(sort_dirs_by_timestamp))

#   # Calculate the number of log directories to remove
#   num_dirs=${#log_dirs[@]}
#   num_dirs_to_remove=$((num_dirs - logfile_keep))
# fi

# Check if there are log directories to remove
# if [ "$num_dirs" -gt 0 ]; then
#   if [ "$num_dirs_to_remove" -gt 0 ]; then
#     echo "Deleting old log directories..."
#     # Loop through the directories and remove the oldest ones
#     for ((i=0; i<$num_dirs_to_remove; i++)); do
#       rm -rf "${log_dirs[$i]}"
#     done
#   else
#     echo "No old log directories to delete."
#   fi
# else
#   echo "No log directories found. Nothing to sort/remove."
# fi

# Known issue communicated to user 
#echo "If experiencing issues, verify permissions for Serial Port"

# Run program
python3 pyAhoiModemManager.py
