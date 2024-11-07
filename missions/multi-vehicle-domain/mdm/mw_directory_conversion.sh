#!/bin/bash
#Example directory conversion script

target_directory="$1"
destination_directory="${1}_tmp"

# python3 ../../MWDataMgr/MWDataMgr.py -d $target_directory/ \
python3 -m mdm -d $target_directory/ \
    -o $destination_directory \
    -t csv json \
    --moos \
    --topic_mapping mwmgr/mw_moos_topic_mapping.cfg 