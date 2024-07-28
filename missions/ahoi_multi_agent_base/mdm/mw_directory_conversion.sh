#!/bin/bash
#Example directory conversion script

target_directory="$1"
destination_directory="${1}_tmp"

python3 -m mdm -d $target_directory/ \
# python3 ../../MWDataMgr/MWDataMgr.py -d $target_directory/ \
python3 -m mdm -d $target_directory/ \
    -o $destination_directory \
    -i mdm/mw_ix.cfg \
    -t json \
    -t csv json \
    --moos \
    --topic_mapping mdm/mw_moos_topic_mapping.cfg 