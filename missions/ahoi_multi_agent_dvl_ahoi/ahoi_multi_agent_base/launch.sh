#!/bin/bash 
#-------------------------------------------------------------- 
#   Script: launch.sh     
#  Mission: convoy_baseline
#   Author: Raymond Turrisi
#   LastEd: Sept. 2023
#-------------------------------------------------------------- 
#  Part 1: Define a convenience function for producing terminal
#          debugging/status output depending on the verbosity.
#-------------------------------------------------------------- 
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }

#-------------------------------------------------------------- 
#  Part 2: Set Global variables
#-------------------------------------------------------------- 
ME=`basename "$0"`
TIME_WARP=1
JUST_MAKE=""
MISSION="convoy_baseline"
MISSION_NAME="$(mhash_gen)/"
VERBOSE=""
AUTO_LAUNCHED="no"
CMD_ARGS=""
LAUNCHGUI=""
NOCONFIRM="-nc"
LOG_RM="no"
LOGDIR_PREF=""

CONFIG_CONDITIONS=""
PARAM_CONDITIONS=""

SHORE_PSHARE="9200"
SHOREIP="localhost"
AMT=6
CNAMT=0
MEDIATED=""

TRANSIT_SPD=1.2
MAXIMUM_SPD=2.0

CONVOY_POLICY=""
TASKBHV=""

CONVOY_VERS=""

USE_CACHE=""
VLAUNCH_ARGS=" --auto "
SLAUNCH_ARGS=" --auto "

#-------------------------------------------------------
#  Part 3: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    CMD_ARGS+=" ${ARGI}"
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "$ME [OPTIONS] [time_warp]                               "
	echo "                                                        "
        echo "Synopsis:                                               "
	echo "  A script for launching an arbitrary number of vehicles"
	echo "                                                        "
	echo "Options:                                                "
        echo "  --help, -h                                            "
        echo "    Display this help message                           "
        echo "  --verbose, -v                                         "
        echo "    Increase verbosity                                  "
	echo "  --just_make, -j                                       " 
	echo "    Just make the targ files, but do not launch.        " 
	echo "  --amt=N                                               " 
	echo "    The number of vehicles to launch. The default is 1. "
	echo "  --cn=N                                                " 
	echo "    The number of contacts to launch. The default is 0. "
	echo "  --gen_number=N                                        "
	echo "    The generator number to use. The default is random. "
	echo "  --active_convoy, -ac                                  " 
	echo "    Use Active Convoy Behavior: BHV_ConvoyV21X          "
	echo "  --nomediate, -nm                                      " 
	echo "    No use of pMediator for inter-vessel comms          "
	echo "  --norand                                              " 
	echo "    Do not randomly generate files vpositions.txt. Just "
	echo "    re-use the previous versions if they exist.         "
	echo "  --shoreip=<ipaddr>                                    " 
	echo "    IP address where nodes can expect to find shoreside "
	echo "  --logclean, -l                                        " 
        echo "    Clean (remove) all log files prior to launch        "
	echo "                                                        "
	exit 0;
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then 
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
        VERBOSE="--verbose"
        NOCONFIRM=""
    elif [ "${ARGI:0:7}" = "--tbhv=" ]; then
        TASKBHV="${ARGI#--tbhv=*}"
        VLAUNCH_ARGS+=" $ARGI"
    elif [ "${ARGI:0:5}" = "--cp=" ]; then
        CONVOY_POLICY="${ARGI#--cp=*}"
        VLAUNCH_ARGS+=" $ARGI"
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        VLAUNCH_ARGS+=" $ARGI"
        SLAUNCH_ARGS+=" $ARGI"
        JUST_MAKE="yes"
    elif [ "${ARGI:0:13}" = "--gen_number=" ]; then
        GEN_NUMBER+=" $ARGI"
    elif [ "${ARGI}" = "--logclean" -o "${ARGI}" = "-l" ]; then
        VLAUNCH_ARGS+=" $ARGI"
    elif [ "${ARGI}" = "--logrm"  ]; then
        LOG_RM="yes"
    elif [ "${ARGI:0:8}" = "--config" ]; then
        CONFIG_CONDITIONS="${ARGI#--config=*}"
    elif [ "${ARGI:0:8}" = "--params" ]; then
        PARAM_CONDITIONS="${ARGI#--params=*}"
    elif [ "${ARGI}" = "--nomediate" -o "${ARGI}" = "-nm" ]; then
        MEDIATED="--nomediate"
    elif [ "${ARGI:0:10}" = "--shoreip=" ]; then
        SHOREIP="${ARGI#--shoreip=*}"
    elif [ "${ARGI:0:8}" = "--shore=" ]; then
        SHOREIP="${ARGI#--shoreip=*}"
    elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
        VLAUNCH_ARGS+=" $ARGI"
    elif [ "${ARGI}" = "--nogui" -o "${ARGI}" = "-n" ]; then
        SLAUNCH_ARGS+=" $ARGI"
    elif [ "${ARGI}" = "--active_convoy" -o "${ARGI}" = "-ac" ]; then
        CONVOY_VERS="--active_convoy"
    elif [ "${ARGI:0:6}" = "--amt=" ]; then
        AMT="${ARGI#--amt=*}"
    elif [ "${ARGI:0:8}" = "--mname=" ]; then
        MISSION_NAME="${ARGI#--mname=*}"
    elif [ "${ARGI:0:7}" = "--pref=" ]; then
        LOGDIR_PREF="${ARGI#--pref=*}"
        MISSION_NAME=$LOGDIR_PREF"_"$MISSION_NAME
	if [ ! $AMT -ge 1 ]; then
	    echo "$ME: Vehicle amount must be >= 1."
	    exit 1
	fi
    else 
	echo "$ME: Bad Arg: $ARGI. Exit Code 1."
	exit 1
    fi
done

echo $@
if [[ $LOG_RM == "yes" ]]; then
    rm -rf logs/*
fi
mkdir logs/${MISSION_NAME}
#---------------------------------------------------------------
#  Part 4: If verbose, show vars and confirm before launching
#---------------------------------------------------------------
if [ "${VERBOSE}" != "" ]; then 
    echo "======================================================"
    echo "              launch.sh SUMMARY                       "
    echo "======================================================"
    echo "$ME"
    echo "CMD_ARGS =      [${CMD_ARGS}]      "
    echo "TIME_WARP =     [${TIME_WARP}]     "
    echo "AUTO_LAUNCHED = [${AUTO_LAUNCHED}] "
    echo "AMT =           [${AMT}]           "
    echo "MEDIATED =      [${MEDIATED}]      "
    echo "---------------------------------- "
    echo "TRANSIT_SPD =   [${TRANSIT_SPD}]   "
    echo "MAXIMUM_SPD =   [${MAXIMUM_SPD}]   "
    echo "CONVOY_VERS =   [${CONVOY_VERS}]   "
    echo "---------------------------------- "
    echo "SHOREIP      =   [${SHOREIP}]      "
    echo -n "Hit the RETURN key to continue with launching"
    read ANSWER
fi

#-------------------------------------------------------------
# Part 5: Generate random starting positions, speeds and vnames
#-------------------------------------------------------------
# TODO: Use PickPos / PickPosX

declare -a VEHPOS
declare -a VNAMES
declare -a COLORS
count=0

if [ "$CONFIG_CONDITIONS" == "" -o  ! -f "agent_configurations.txt" ]; then 
    #python3 generators/generator_set1_configs.py $RANDOM
    CONFIG_CONDITIONS="agent_configurations.txt"
fi 

while IFS=, read -r name x y hdg color || [[ -n $name ]]; do 
    # Combine the second and third columns for VEHPOS

    if [[ $name =~ ^# ]]; then
        continue 
    fi

    veh_pos="x=$x,y=$y,heading=$hdg"
    veh_pos="${veh_pos// /}"
    # Append the parsed values to the arrays
    VEHPOS+=("$veh_pos")
    name="${name// /}"

    VNAMES+=("$name")
    color="${color// /}"
    COLORS+=("$color")
    ((count++))
done < $CONFIG_CONDITIONS
AMT=$count

if [ "$PARAM_CONDITIONS" == "" -a  ! -f "plug_bhv_variables.moos" ]; then 
    #Nothing to do yet
    ub=$(python3 generators/generator_set1_params.py --ub)
    if [[ GEN_NUMBER -gt $ub ]]; then
        idx="$(( RANDOM % $ub ))"
    elif [[ GEN_NUMBER -lt 0 ]]; then
        idx="$(( RANDOM % $ub ))"
    else
        idx=$GEN_NUMBER
    fi
    idx="$(( RANDOM % $ub ))"
    python3 generators/generator_set1_params.py $idx
    PARAM_CONDITIONS="plug_bhv_variables.moos"
fi 

#-------------------------------------------------------------
# Part 7: Launch the convoy vehicles
#-------------------------------------------------------------

VLAUNCH_ARGS+=" $NOCONFIRM "
ALL_VNAMES=""
for INDEX in `seq 1 $AMT`;
do
    sleep 0.2
    ARRAY_INDEX=`expr $INDEX - 1`
    START=${VEHPOS[$ARRAY_INDEX]}
    VNAME=${VNAMES[$ARRAY_INDEX]}
    COLOR=${COLORS[$ARRAY_INDEX]}

    if [ "${ALL_VNAMES}" != "" ]; then
	ALL_VNAMES+=":"
    fi
    ALL_VNAMES+=$VNAME
    
    IX_VLAUNCH_ARGS=$VLAUNCH_ARGS
    IX_VLAUNCH_ARGS+=" --index=$INDEX --start=$START    "
    IX_VLAUNCH_ARGS+=" --maxspd=$MAXIMUM_SPD            "
    IX_VLAUNCH_ARGS+=" --speed=$TRANSIT_SPD             " 
    IX_VLAUNCH_ARGS+=" --color=$COLOR  --sim            " 
    IX_VLAUNCH_ARGS+=" --vname=$VNAME  --shore=$SHOREIP "
    IX_VLAUNCH_ARGS+=" $VERBOSE $CONVOY_VERS $MEDIATED  "
    IX_VLAUNCH_ARGS+=" $TIME_WARP "

    #vecho "Launching: $VNAME"
	./launch_vehicle.sh $IX_VLAUNCH_ARGS --mname=$MISSION_NAME
done

#-------------------------------------------------------------
# Part 7: Launch the Shoreside mission file
#-------------------------------------------------------------
vecho "Launching the shoreside. Args: $SLAUNCH_ARGS $TIME_WARP"

SLAUNCH_ARGS+=" --vnames=$ALL_VNAMES "

./launch_shoreside.sh $SLAUNCH_ARGS $VERBOSE $TIME_WARP --mname=$MISSION_NAME
sleep 0.25

#---------------------------------------------------------------
#  Part 8: If launched from script, we're done, exit now
#---------------------------------------------------------------
if [ "${AUTO_LAUNCHED}" = "yes" -o "${JUST_MAKE}" != "" ]; then
    exit 0
fi

#-------------------------------------------------------------
# Part 9: Launch uMAC in paused mode until the mission is quit
#-------------------------------------------------------------
uMAC --paused targs/targ_shoreside.moos
kill -- -$$
