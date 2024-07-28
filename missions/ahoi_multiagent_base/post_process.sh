

# Strip variables worth ignoring from a mission

newest_mission=(logs/$1*)
newest_mission=${newest_mission[0]}

rm -rf $newest_mission/**/**.blog $newest_mission/**/**.ylog

deletions="\
    DB_EVENT \
    DB_CLIENTS \
    DB_UPTIME \
    DB_TIME \
    LOGGER_DIRECTORY \
    APPCAST \
    PSHARE_INPUT_SUMMARY \
    PSHARE_OUTPUT_SUMMARY \
    APPCAST_REQ \
    ACK_MESSAGE \
    ACK_MESSAGE_LOCAL \
    OPR_TRAJECTORY_PERIM_ETA \
    UMH_SUMMARY_MSGS \
    NODE_PSHARE_VARS \
    APP_LOG \
    PROC_WATCH_TIME_WARP \
    PROC_WATCH_EVENT \
    PROC_WATCH_ALL_OK \
    PROC_WATCH_SUMMARY \
    PROC_WATCH_FULL_SUMMARY \
    IVPHELM_LOOP_CPU \
    IVPHELM_CREATE_CPU \
    IVPHELM_ITER \
    IVPHELM_TOTAL_PCS_CACHED \
    IVPHELM_TOTAL_PCS_FORMED \
    IVPHELM_IPF_CNT \
    IVPHELM_SUMMARY \
    HELM_MAP_CLEAR \
    PNODEREPORTER_PID \
    UFLDNODEBROKER_PID \
    PSHARE_CMD \
    LOGGER_DIRECTORY \
    PID_REPORT \
    UMH_SUMMARY_MSGS \
    NODE_BROKER_ACK \
    NODE_PSHARE_VARS \
    MISSION_HASH \
    HELM_MAP_CLEAR \
    REALMCAST_CHANNELS \
    IVPHELM_REGISTER \
    CONTACTS_RECAP \
    CONTACT_RANGES \
    PCONTACTMGRV20_PID \
    IVPHELM_CPU \
    PNR_EXTRAP_POS_GAP \
    PNR_EXTRAP_HDG_GAP \
    BHV_IPF \
    BHV_EVENT \
    OPR_SECS_IN_POLY \
    OPR_DEBUG \
    OPR_TRAJECTORY_PERIM_DIST \
    COMMS_POLICY \
    PLOGGER_CMD \
    TM_ALERT_REQUEST \
    BCM_ALERT_REQUEST \
    MOOS_DEBUG \
    VIEW_POINT \
    TAIL_SIZE \
    HM_SIZE \
    MEDIATED_MESSAGE \
    MEDIATED_MESSAGE* \
    MEDIATED_MESSAGE_LOCAL \
    NAV_HEADING_OVER_GROUND \
    NAV_LAT \
    NAV_LONG \
    HIT_MARKER \
    IVPHELM_UPDATE_RESULT \
    PNR_POST_GAP \
    OPR_ABSOLUTE_PERIM_DIST \
    OPR_ABSOLUTE_PERIM_ETA \
    ALERT_VERBOSE \
    VIEW_COMMS_PULSE \
    UFSB_BRIDGE_VARS \
    *_ITER_LEN \
    *_ITER_GAP \
    DB_QOS \
    ACK_MESSAGE_* \
    PHOSTINFO_ITER_GAP \
    PHOSTINFO_ITER_LEN \
    UPROCESSWATCH_ITER_GAP \
    UPROCESSWATCH_ITER_LEN \
    UFLDSHOREBROKER_ITER_GAP \
    UFLDSHOREBROKER_ITER_LEN \
    NODE_BROKER_PING \
    PREALM_ITER_GAP \
    PREALM_ITER_LEN \
    UFLDTASKMONITOR_ITER_GAP \
    UFLDTASKMONITOR_ITER_LEN \
    UXMS_838_ITER_GAP \
    UXMS_838_ITER_LEN \
    UFLDCOLLISIONDETECT_ITER_GAP \
    UFLDCOLLISIONDETECT_ITER_LEN \
    "

for DIR in $newest_mission/*; do
    for alog in $DIR/*.alog; do 
        mv $alog ${alog}-old
        alogrm -f -q ${alog}-old $deletions $alog
        rm ${alog}-old
    done 
    
done

#TODO: Check to make sure this runs okay
# > Run MWDataMgr.py to get CSV files of agent names, and nav positions
./mdm/mw_directory_conversion.sh $newest_mission

#TODO: Check to make sure this runs okay, it may fail if a mission did not run as expected, and if it fails, we need to put the mission hash into a failed directory, i.e. 00_failed/
# > Run another Python script for composing a plot with relevant information
python3 analyze.py ${newest_mission}

#If our analysis script fails, we remove the meta directory, but zip the mission to observe what happened later. 
if [ $? -ne 0 ]; then
    m_id=${newest_mission#*/}
    m_id=${m_id%_meta}
    mkdir -p logs/failed
    7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on logs/failed/$newest_mission.7z ${newest_mission} &> /dev/null
    rmdir ${newest_mission}_meta
    echo "$m_id" >> logs/failed.txt
fi 

rm -rf ${newest_mission}_tmp
# Do we want to save good data? 
#7z a -t7z -m0=lzma -mx=9 -mfb=64 -md=32m -ms=on $newest_mission.7z $newest_mission &> /dev/null
rm -rf $newest_mission