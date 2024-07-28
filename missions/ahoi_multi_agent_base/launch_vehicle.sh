#!/bin/bash
#-------------------------------------------------------------- 
#   Script: launch_vehicle.sh    
#  Mission: convoy_ct
#   Author: Michael Benjamin   
#   LastEd: November 2021
#-------------------------------------------------------------- 
#  Part 1: Define a convenience function for producing terminal
#          debugging/status output depending on the verbosity.
#-------------------------------------------------------------- 
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }

#-------------------------------------------------------------- 
#  Part 2: Set Global Variables
#-------------------------------------------------------------- 

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

#SHORE_IP="192.168.1.224"
SHORE_IP="192.168.1.77"
SHORE_PSHARE="9200"
VNAME=""
COLOR="gray70"
INDEX="1"
XMODE="M300"
MEDIATED="yes"
CONVOY_POLICY=""
TASKBHV=""

REGION="pavlab"
START_POS="0,0,180"  
RETURN_POS="5,0"
TRANSIT_SPD="1.2"  
MAXIMUM_SPD="2"
CONVOY_ACTIVE="true"

MTASC=""
LOG_CLEAN="no"

LEADIN_POS="-72,-67"
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
        echo "  --mtasc, -m                                    "
        echo "     Mission is remotely launched (e.g. MTASC)   "
        echo "  --active_convoy, -ac                           "
        echo "     Set active_convoying=true in BHV_ConvoyV21X "
	echo "                                                 "
        echo "  --abe,  -A  : abe vehicle.                     "
        echo "  --ben,  -B  : ben vehicle.                     "
        echo "  --cal,  -C  : cal vehicle.                     "
        echo "  --deb,  -D  : deb vehicle.                     "
	echo "  --eve,  -E  : eve vehicle.                     "
        echo "  --fin,  -F  : fin vehicle.                     "
	echo "  --max,  -M  : max vehicle.                     "
        echo "  --ned,  -N  : ned vehicle.                     "
	echo "  --oak,  -O  : oak vehicle.                     "
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
    elif [ "${ARGI}" = "--mtasc" -o "${ARGI}" = "-m" ]; then
	MTASC="yes"

    elif [ "${ARGI}" = "--abe" -o "${ARGI}" = "-A" ]; then
        VNAME="abe"
    elif [ "${ARGI}" = "--ben" -o "${ARGI}" = "-B" ]; then
        VNAME="ben"
    elif [ "${ARGI}" = "--cal" -o "${ARGI}" = "-C" ]; then
        VNAME="cal"
    elif [ "${ARGI}" = "--deb" -o "${ARGI}" = "-D" ]; then
        VNAME="deb"
    elif [ "${ARGI}" = "--eve" -o "${ARGI}" = "-E" ]; then
        VNAME="eve"
    elif [ "${ARGI}" = "--fin" -o "${ARGI}" = "-F" ]; then
        VNAME="fin"
    elif [ "${ARGI}" = "--max" -o "${ARGI}" = "-M" ]; then
        VNAME="max"
    elif [ "${ARGI}" = "--ned" -o "${ARGI}" = "-N" ]; then
        VNAME="ned"
    elif [ "${ARGI}" = "--oak" -o "${ARGI}" = "-O" ]; then
        VNAME="oak"
	
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
    elif [ "${ARGI:0:8}" = "--speed=" ]; then
        TRANSIT_SPD="${ARGI#--speed=*}"
    elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
        MAXIMUM_SPD="${ARGI#--maxspd=*}"
    elif [ "${ARGI:0:7}" = "--tbhv=" ]; then
        TASKBHV="${ARGI#--tbhv=*}"
    elif [ "${ARGI:0:5}" = "--cp=" ]; then
        CONVOY_POLICY="${ARGI#--cp=*}"

    elif [ "${ARGI}" = "--active_convoy" -o "${ARGI}" = "-ac" ]; then
	CONVOY_VERS="active"

    elif [ "${ARGI}" = "--sim" -o "${ARGI}" = "-s" ]; then
        XMODE="SIM"
        echo "Simulation mode ON."
    else 
	echo "$ME: Bad Arg:[$ARGI]. Exit Code 1."
	exit 1
    fi
done

#--------------------------------------------------------------
#  Part 3B: Check for VNAME. Use INDEX for Other Settings
#--------------------------------------------------------------
if [ -z $VNAME ]; then
    if [ "${XMODE}" = "SIM" ]; then
	VNAME="abe"
    else
	echo "No in-water vehicle selected. Exit Code 2."
	exit 2
    fi
fi

if [ "${VNAME}" = "abe" ]; then
    INDEX=14
elif [ "${VNAME}" = "ben" ]; then
    INDEX=15
elif [ "${VNAME}" = "cal" ]; then
    INDEX=16
elif [ "${VNAME}" = "deb" ]; then
    INDEX=17
elif [ "${VNAME}" = "eve" ]; then
    INDEX=18
elif [ "${VNAME}" = "fin" ]; then
    INDEX=19
elif [ "${VNAME}" = "max" ]; then
    INDEX=20
elif [ "${VNAME}" = "ned" ]; then
    INDEX=21
elif [ "${VNAME}" = "oak" ]; then
    INDEX=22
fi

MOOS_PORT=`expr $INDEX + 9000`
PSHARE_PORT=`expr $INDEX + 9200`
FSEAT_IP="192.168.$INDEX.1"

if [ "${XMODE}" = "SIM" ]; then
    if [ "${MTASC}" = "yes" ]; then
	if [ "${IP_ADDR}" = "localhost" ]; then
	    echo "IP_ADDR missing on vehicle in MTASC mode "
	    echo "The --ip=<addr> arg should be provided   "
	    exit 1
	fi
    else
	IP_ADDR="localhost"
	SHORE_IP="localhost"
    fi
else
    IP_ADDR="192.168.$INDEX.100"
fi
    

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
    echo "FSEAT_IP =       [${FSEAT_IP}]      "
    echo "XMODE =          [${XMODE}]         "
    echo "MTASC =          [${MTASC}]         "
    echo "MEDIATED =       [${MEDIATED}]      "
    echo "----------------------------------  "
    echo "START_POS =      [${START_POS}]     "
    echo "TRANSIT_SPD =    [${TRANSIT_SPD}]   "
    echo "MAXIMUM_SPD =    [${MAXIMUM_SPD}]   "
    echo "CONVOY_ACTIVE =  [${CONVOY_ACTIVE}] "
    echo "CONVOY_POLICY =  [${CONVOY_POLICY}] "
    echo "TASKBHV =  [${TASKBHV}] "
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
       FSEAT_IP=$FSEAT_IP           XMODE=$XMODE                 \
       MEDIATED=$MEDIATED           MISSION_NAME=$MISSION_NAME   \
       
nsplug meta_vehicle.bhv targs/targ_$VNAME.bhv $NSFLAGS VNAME=$VNAME    \
       TRANSIT_SPD=$TRANSIT_SPD     COLOR=$COLOR                 \
       CONVOY_ACTIVE=$CONVOY_ACTIVE LEADIN_POS=$LEADIN_POS \
       CONVOY_POLICY=$CONVOY_POLICY  TASKBHV=$TASKBHV
       
if [ "${JUST_MAKE}" = "yes" ]; then
    vecho "Files assembled; nothing launched; exiting per request."
    exit 0
fi

#-------------------------------------------------------
#  Part 7: Launch the vehicle mission
#-------------------------------------------------------
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
uMAC targs/targ_$VNAME.moos
kill -- -$$
