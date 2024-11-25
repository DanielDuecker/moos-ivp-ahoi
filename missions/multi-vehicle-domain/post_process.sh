

# Strip variables worth ignoring from a mission

mission_directory=$1

rm -rf $mission_directory/*/*.blog $mission_directory/*/*.ylog

thin_logdir $mission_directory/LOG_SEASCOUT-*

eval ./mdm/mw_directory_conversion.sh $mission_directory/LOG_SEASCOUT-*

python3 analyze_00.py ${mission_directory}
python3 analyze_00_nav.py ${mission_directory}

rm -rf "${mission_directory}_tmp"
