#!/bin/bash
#-------------------------------------------------------------- 
#   Script: launch_vehicle.sh    
#  Mission: alpha_seascout
#   Author: Raymond Turrisi
#   LastEd: April 2024

#-------------------------------------------------------------- 
#  Part 1: Define a convenience function for producing terminal
#          debugging/status output depending on the verbosity.
#-------------------------------------------------------------- 
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }

#-------------------------------------------------------------- 
#  Part 2: Set Global Variables
#------in-------------------------------------------------------- 

ME=`basename "$0"`
TIME_WARP=1
VERBOSE=""
JUST_MAKE="no"
CONFIRM="yes"
AUTO_LAUNCHED="no"
CMD_ARGS=""

IP_ADDR="localhost"
MOOS_PORT="9001"
PSHARE_PORT="9201"

SHORE_IP="localhost"
SHORE_PSHARE="9200"
VNAME=$(hostname)
COLOR="gray70"
INDEX="1"
XMODE="SEASCOUT"
MEDIATED="yes"

START_POS="0,0,180"  
TRANSIT_SPD="1.2"  
MAXIMUM_SPD="2"
MAXIMUM_DEPTH="5"

MTASC=""
LOG_CLEAN="no"

HEADLESS="no"

MISSION_NAME=""
#-------------------------------------------------------
#  Part 3: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    CMD_ARGS+=" ${ARGI}"
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "$ME: [OPTIONS] [time_warp]                       "
	echo "                                                 "
	echo "Options:                                         "
	echo "  --help, -h                                     " 
	echo "    Print this help message and exit             "
	echo "  --just_make, -j                                " 
	echo "    Just make targ files, but do not launch      "
	echo "  --verbose, -v                                  " 
	echo "    Verbose output, confirm before launching     "
	echo "  --noconfirm, -nc                               " 
	echo "    No confirmation before launching             "
	echo "  --nomediate, -nm                               " 
	echo "    No use of pMediator for inter-vessel comms   "
        echo "  --auto, -a                                     "
        echo "     Auto-launched by a script.                  "
        echo "     Will not launch uMAC as the final step.     "
	echo "                                                 "
	echo "  --ip=<localhost>                               " 
	echo "    Force pHostInfo to use this IP Address       "
	echo "  --mport=<9001>                                 "
	echo "    Port number of this vehicle's MOOSDB port    "
	echo "  --pshare=<9201>                                " 
	echo "    Port number of this vehicle's pShare port    "
	echo "                                                 "
	echo "  --shore=<localhost>                            " 
	echo "    IP address location of shoreside             "
	echo "  --shore_pshare=<9200>                          " 
	echo "    Port on which shoreside pShare is listening  "
	echo "  --vname=<abe>                                  " 
	echo "    Name of the vehicle being launched           " 
	echo "  --index=<1>                                    " 
	echo "    Index for setting MOOSDB and pShare ports    "
	echo "                                                 "
	echo "  --start=<X,Y,H>     (default is 0,0,180)       " 
	echo "    Start position chosen by script launching    "
	echo "    this script (to ensure separation)           "
	echo "  --speed=meters/sec                             " 
	echo "    The speed use for transiting/loitering       "
	echo "                                                 "
	echo "  --maxspd=meters/sec                            " 
	echo "    Max speed of vehicle (for sim and in-field)  "
	exit 0;
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then 
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        JUST_MAKE="yes"
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
        VERBOSE="yes"
    elif [ "${ARGI}" = "--noconfirm" -o "${ARGI}" = "-nc" ]; then
	CONFIRM="no"
    elif [ "${ARGI}" = "--nomediate" -o "${ARGI}" = "-nm" ]; then
	MEDIATED="no"
    elif [ "${ARGI}" = "--auto" -o "${ARGI}" = "-a" ]; then
        AUTO_LAUNCHED="yes"
    elif [ "${ARGI}" = "--logclean" -o "${ARGI}" = "-l" ]; then
	LOG_CLEAN="yes"
    elif [ "${ARGI:0:5}" = "--ip=" ]; then
        IP_ADDR="${ARGI#--ip=*}"
    elif [ "${ARGI:0:7}" = "--mport" ]; then
	MOOS_PORT="${ARGI#--mport=*}"
    elif [ "${ARGI:0:9}" = "--pshare=" ]; then
        PSHARE_PORT="${ARGI#--pshare=*}"
    elif [ "${ARGI:0:8}" = "--shore=" ]; then
        SHORE_IP="${ARGI#--shore=*}"
    elif [ "${ARGI:0:15}" = "--shore_pshare=" ]; then
        SHORE_PSHARE="${ARGI#--shore_pshare=*}"
    elif [ "${ARGI:0:8}" = "--mname=" ]; then
        MISSION_NAME="${ARGI#--mname=*}"
    elif [ "${ARGI:0:8}" = "--vname=" ]; then
        VNAME="${ARGI#--vname=*}"
    elif [ "${ARGI:0:8}" = "--color=" ]; then
        COLOR="${ARGI#--color=*}"
    elif [ "${ARGI:0:8}" = "--index=" ]; then
        INDEX="${ARGI#--index=*}"
    elif [ "${ARGI:0:8}" = "--start=" ]; then
        START_POS="${ARGI#--start=*}"
    elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
        MAXIMUM_SPD="${ARGI#--maxspd=*}"
    elif [ "${ARGI:0:9}" = "--maxdepth=" ]; then
        MAXIMUM_DEPTH="${ARGI#--maxdepth=*}"
    elif [ "${ARGI:0:10}" = "--headless" ]; then
        HEADLESS="yes"
    elif [ "${ARGI:0:6}" = "--hitl" ]; then
        XMODE="HITL"
    elif [ "${ARGI}" = "--sim" -o "${ARGI}" = "-s" ]; then
        XMODE="SIM"
        INDEX="2"
        echo "Simulation mode ON."
    else 
	echo "$ME: Bad Arg:[$ARGI]. Exit Code 1."
	exit 1
    fi
done

MOOS_PORT=`expr $INDEX + 9000`
PSHARE_PORT=`expr $INDEX + 9200`

#---------------------------------------------------------------
#  Part 4: If verbose, show vars and confirm before launching
#---------------------------------------------------------------
if [ "${VERBOSE}" = "yes" -o "${CONFIRM}" = "yes" ]; then 
    echo "==========================================="
    echo "     launch_vehicle.sh SUMMARY      $VNAME "
    echo "==========================================="
    echo "$ME"
    echo "CMD_ARGS =       [${CMD_ARGS}]      "
    echo "TIME_WARP =      [${TIME_WARP}]     "
    echo "AUTO_LAUNCHED =  [${AUTO_LAUNCHED}] "
    echo "----------------------------------  "
    echo "MOOS_PORT =      [${MOOS_PORT}]     "
    echo "PSHARE_PORT =    [${PSHARE_PORT}]   "
    echo "IP_ADDR =        [${IP_ADDR}]       "
    echo "----------------------------------  "
    echo "SHORE_IP =       [${SHORE_IP}]      "
    echo "SHORE_PSHARE =   [${SHORE_PSHARE}]  "
    echo "VNAME =          [${VNAME}]         "
    echo "COLOR =          [${COLOR}]         "
    echo "INDEX =          [${INDEX}]         "
    echo "----------------------------------  "
    echo "XMODE =          [${XMODE}]         "
    echo "MTASC =          [${MTASC}]         "
    echo "MEDIATED =       [${MEDIATED}]      "
    echo "----------------------------------  "
    echo "START_POS =      [${START_POS}]     "
    echo "MAXIMUM_SPD =    [${MAXIMUM_SPD}]   "
    echo "MAXIMUM_DEPTH =    [${MAXIMUM_DEPTH}]   "
    echo -n "Hit the RETURN key to continue with launching"
    read ANSWER
fi

#-------------------------------------------------------
#  Part 5: If Log clean before launch, do it now. 
#          In MTASC missions, remote cleaning is essential.
#-------------------------------------------------------
if [ "$LOG_CLEAN" = "yes" ]; then
    vecho "Cleaning local Log Files"
    rm -rf LOG* XLOG* MOOSLog*
fi

if [ "$MISSION_NAME" = "" ]; then
    MISSION_NAME=$(mhash_gen)
    mkdir logs/$MISSION_NAME
fi

#-------------------------------------------------------
#  Part 6: Create the .moos and .bhv files. 
#-------------------------------------------------------
# interactive nsplug only when not being remotely launched.
NSFLAGS="-s -f"
if [ "${AUTO_LAUNCHED}" = "no" ]; then
    NSFLAGS="-i -f"
fi

mkdir targs &> /dev/null

nsplug meta_vehicle.moos targs/targ_$VNAME.moos $NSFLAGS WARP=$TIME_WARP  \
       PSHARE_PORT=$PSHARE_PORT     VNAME=$VNAME                 \
       COLOR=$COLOR                 MAXSPD=$MAXSPD               \
       START_POS=$START_POS         SHORE_IP=$SHORE_IP           \
       SHORE_PSHARE=$SHORE_PSHARE   MOOS_PORT=$MOOS_PORT         \
       IP_ADDR=$IP_ADDR             MAXIMUM_SPD=$MAXIMUM_SPD     \
       MAXIMUM_DEPTH=$MAXIMUM_DEPTH     START_POS=$START_POS     \
       MEDIATED=$MEDIATED           MISSION_NAME=$MISSION_NAME   \
       XMODE=$XMODE \
       --macros=/home/pi/moos-ivp-seascout/data/$(hostname)/profile.moos
       
nsplug meta_vehicle.bhv targs/targ_$VNAME.bhv $NSFLAGS VNAME=$VNAME    \
       MAXIMUM_DEPTH=$MAXIMUM_DEPTH XMODE=$XMODE

if [ "${JUST_MAKE}" = "yes" ]; then
    vecho "Files assembled; nothing launched; exiting per request."
    exit 0
fi

#-------------------------------------------------------
#  Part 7: Launch the vehicle mission
#-------------------------------------------------------

# Check system state to make sure that the vehicle should be run.
if [ "$XMODE" != "HITL" ]; then
    vecho "Running pre-mission checks..."
    
    # Run the pre-mission check script
    pre-mission-check.sh
    check_result=$?
    
    # Check if the pre-mission script passed
    if [ "$check_result" -ne 0 ]; then
        vecho "Pre-mission checks failed. Aborting launch."
        exit 1
    else
        vecho "Pre-mission checks passed. Proceeding with launch."
    fi
else
    vecho "Hardware-in-the-loop (HITL) mode detected. Skipping pre-mission checks."
fi

ts=$(date '+%Y%m%d_%H%M%S')
echo "$ts Vehicle launched in headless mode successfully" >> ~/moos-ivp-seascout/data/$(hostname)/logs/history.log

vecho "Launching $VNAME MOOS Community. WARP="$TIME_WARP
pAntler targs/targ_$VNAME.moos >& /dev/null &
vecho "Done Launching $VNAME MOOS Community"

#---------------------------------------------------------------
#  Part 8: If launched from script, we're done, exit now
#---------------------------------------------------------------
if [ "${AUTO_LAUNCHED}" = "yes" ]; then
    exit 0
fi

#---------------------------------------------------------------
# Part 9: Launch uMAC until the mission is quit
#---------------------------------------------------------------

# If we run in headless mode, the vehicle will automatically close the mission down after several conditions
if [ "${HEADLESS}" = "no" ]; then
    uMAC targs/targ_$VNAME.moos
else
    DONE="false"
    IN_WATER="false"
    while [ "${DONE}" = "false" ]; do
        echo "Mission Running..."
        # We shut down if the autonomy missions are complete
        if uQueryDB targs/targ_$VNAME.moos --condition="MISSION_COMPLETE == true" --wait=2 >& /dev/null; then
            echo "Mission Complete - Quitting"
            uPokeDB targs/targ_$VNAME.moos MOOS_MANUAL_OVERRIDE_ALL=false
            DONE="true"
            break
        # We shut down if the vehicle is removed from the water, after it was set. This checks that locally we have recognized that the vehicle was in the water, and that now we have removed it from the water
        elif [ "$IN_WATER" = "true" ] && uQueryDB targs/targ_$VNAME.moos --condition="IN_WATER == false" --wait=2 >& /dev/null; then
            echo "Vehicle has left the water - Shutting Down"
            uPokeDB targs/targ_$VNAME.moos MOOS_MANUAL_OVERRIDE_ALL=false
            DONE="true"
            break
        else
            # We check if the vehicle is in the water
            if [ "$IN_WATER" = "false" ] && uQueryDB targs/targ_$VNAME.moos --condition="IN_WATER == true" --wait=2 >& /dev/null; then
                IN_WATER="true"
            fi
            sleep 5
        fi
    done
fi

ts=$(date '+%Y%m%d_%H%M%S')
echo "$ts Vehicle is shutting down processes post-mission" >> ~/moos-ivp-seascout/data/$(hostname)/logs/history.log

test_led --set 0 255 0 0

kill -- -$$

sleep 5

test_led --set 0 255 0 0

sleep 2