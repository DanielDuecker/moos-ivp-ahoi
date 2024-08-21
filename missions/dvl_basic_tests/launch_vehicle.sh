#!/bin/bash
#-------------------------------------------------------------- 
#   Script: launch_vehicle.sh                                    
#  Mission: alpha_heron
#   Author: Michael Benjamin  
#     Date: June 2021
#--------------------------------------------------------------
#  Part 1: Declare global var defaults
#--------------------------------------------------------------
ME=`basename "$0"`
TIME_WARP=1
JUST_MAKE="no"
VERBOSE="no"
CONFIRM="yes"
AUTO_LAUNCHED="no"
CMD_ARGS=""

IP_ADDR="localhost"
MOOS_PORT="9001"
PSHARE_PORT="9201"

SHORE_IP="192.168.1.241"
SHORE_PSHARE="9200"
VNAME=""
INDEX="1"
XMODE="M300"

REGION="pavlab"
START_POS="0,0,180"
SPEED="1.0"
RETURN_POS="5,0"
MAXSPD="2"

ZONE=""

#--------------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#--------------------------------------------------------------
for ARGI; do
    CMD_ARGS+=" ${ARGI}"
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "$ME [OPTIONS] [time_warp]                        "
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
	echo "  --start=<X,Y>     (default is 0,0)             " 
	echo "    Start position chosen by script launching    "
	echo "    this script (to ensure separation)           "
	echo "  --speed=meters/sec                             " 
	echo "    The speed use for transiting/loitering       "
	echo "  --maxspd=meters/sec                            " 
	echo "    Max speed of vehicle (for sim and in-field)  "
	echo "                                                 "
	echo "  --east, -e                                     " 
	echo "    Vehicle traverses the east zone              "
	echo "  --west, -w                                     " 
	echo "    Vehicle traverses the west zone              "
	echo "                                                 "
	echo "  --abe,  -A  : abe vehicle.                     "
	echo "  --ben,  -B  : ben vehicle.                     "
	echo "  --cal,  -C  : cal vehicle.                     "
	echo "  --deb,  -D  : deb vehicle.                     "
	echo "  --eve,  -E  : eve vehicle.                     "
	echo "  --fin,  -F  : fin vehicle.                     "
	echo "  --max,  -M  : max vehicle.                     "
	echo "  --ned,  -N  : ned vehicle.                     "
    echo "  --oak,  -O  : oak vehicle.                         "
    echo "  -MM  : cpr-m300-0020 vehicle.                      "
    echo "  -NN  : cpr-m300-0021 vehicle.                      "
    echo "  -OO  : cpr-m300-0022 vehicle.                      "
	echo "  --m300       : Use iM300 interface             "
	exit 0;
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
	JUST_MAKE="yes"
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
        VERBOSE="yes"
    elif [ "${ARGI}" = "--noconfirm" -o "${ARGI}" = "-nc" ]; then
	CONFIRM="no"
    elif [ "${ARGI}" = "--auto" -o "${ARGI}" = "-a" ]; then
        AUTO_LAUNCHED="yes" 

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
    elif [ "${ARGI:0:8}" = "--vname=" ]; then
        VNAME="${ARGI#--vname=*}"
    elif [ "${ARGI:0:8}" = "--index=" ]; then
        INDEX="${ARGI#--index=*}"

    elif [ "${ARGI:0:8}" = "--start=" ]; then
        START_POS="${ARGI#--start=*}"
    elif [ "${ARGI:0:8}" = "--speed=" ]; then
        SPEED="${ARGI#--speed=*}"
    elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
        MAXSPD="${ARGI#--maxspd=*}"

	
    elif [ "${ARGI}" = "--abe" -o "${ARGI}" = "-A" ]; then
        VNAME="abe"
	INDEX=14
    elif [ "${ARGI}" = "--ben" -o "${ARGI}" = "-B" ]; then
        VNAME="ben"
	INDEX=15
    elif [ "${ARGI}" = "--cal" -o "${ARGI}" = "-C" ]; then
        VNAME="cal"
	INDEX=16
    elif [ "${ARGI}" = "--deb" -o "${ARGI}" = "-D" ]; then
        VNAME="deb"
	INDEX=17
    elif [ "${ARGI}" = "--eve" -o "${ARGI}" = "-E" ]; then
        VNAME="eve"
	INDEX=18
    elif [ "${ARGI}" = "--fin" -o "${ARGI}" = "-F" ]; then
        VNAME="fin"
	INDEX=19
    elif [ "${ARGI}" = "--max" -o "${ARGI}" = "-M" ]; then
        VNAME="max"
	INDEX=20
    elif [ "${ARGI}" = "--ned" -o "${ARGI}" = "-N" ]; then
        VNAME="ned"
	INDEX=21
    elif [ "${ARGI}" = "--oak" -o "${ARGI}" = "-O" ]; then
        VNAME="oak"
    INDEX=22
    elif [ "${ARGI}" = "-MM" ]; then
        VNAME="cpr-m300-0020"
    INDEX=22
    elif [ "${ARGI}" = "-NN" ]; then
        VNAME="cpr-m300-0021"
    INDEX=15
    elif [ "${ARGI}" = "-OO" ]; then
        VNAME="cpr-m300-0022"
    INDEX=16

    elif [ "${ARGI}" = "--sim" -o "${ARGI}" = "-s" ]; then
        XMODE="SIM"
        echo "Simulation mode ON."

    elif [ "${ARGI}" = "--west" -o "${ARGI}" = "-w" ]; then
        ZONE="west" 
    elif [ "${ARGI}" = "--east" -o "${ARGI}" = "-e" ]; then
        ZONE="east" 
    else
	echo "$ME: Bad Arg:[$ARGI]. Exit Code 1."
	exit 1
    fi
done

#--------------------------------------------------------------
#  Part 3: Check for VNAME. Use INDEX for Other Settings
#--------------------------------------------------------------
if [ -z $VNAME ]; then
    if [ "${XMODE}" = "SIM" ]; then
	VNAME="abe"
    else
	echo "No in-water vehicle selected. Exit Code 2."
	exit 2
    fi
fi

MOOS_PORT=`expr $INDEX + 9000`
PSHARE_PORT=`expr $INDEX + 9200`
FSEAT_IP="192.168.$INDEX.1"
IP_ADDR="192.168.$INDEX.100"

if [ "${XMODE}" = "SIM" ]; then
    IP_ADDR="localhost"
    SHORE_IP="localhost"
fi


#---------------------------------------------------------------
#  Part 4: If verbose, show vars and confirm before launching
#---------------------------------------------------------------
if [ "${VERBOSE}" = "yes" -o "${CONFIRM}" = "yes" ]; then 
    echo "$ME"
    echo "CMD_ARGS =      [${CMD_ARGS}]     "
    echo "TIME_WARP =     [${TIME_WARP}]    "
    echo "AUTO_LAUNCHED = [${AUTO_LAUNCHED}]"
    echo "----------------------------------"
    echo "MOOS_PORT =     [${MOOS_PORT}]    "
    echo "PSHARE_PORT =   [${PSHARE_PORT}]  "
    echo "IP_ADDR =       [${IP_ADDR}]      "
    echo "----------------------------------"
    echo "SHORE_IP =      [${SHORE_IP}]     "
    echo "SHORE_PSHARE =  [${SHORE_PSHARE}] "
    echo "VNAME =         [${VNAME}]        "
    echo "INDEX =         [${INDEX}]        "
    echo "----------------------------------"
    echo "FSEAT_IP =      [${FSEAT_IP}]     "
    echo "XMODE =         [${XMODE}]        "
    echo "----------------------------------"
    echo "START_POS =     [${START_POS}]    "
    echo "SPEED =         [${SPEED}]        "
    echo "MAXSPD =        [${MAXSPD}]       "
    echo "ZONE =          [${ZONE}]         "
    echo -n "Hit any key to continue with launching"
    read ANSWER
fi


#--------------------------------------------------------------
#  Part 5: Create the .moos and .bhv files. 
#--------------------------------------------------------------
NSFLAGS="-s -f"
if [ "${AUTO}" = "" ]; then
    NSFLAGS="-i -f"
fi

nsplug meta_vehicle.moos targ_$VNAME.moos $NSFLAGS WARP=$TIME_WARP \
       PSHARE_PORT=$PSHARE_PORT     VNAME=$VNAME               \
       START_POS=$START_POS         SHORE_IP=$SHORE_IP         \
       SHORE_PSHARE=$SHORE_PSHARE   MOOS_PORT=$MOOS_PORT       \
       IP_ADDR=$IP_ADDR             REGION=$REGION             \
       FSEAT_IP=$FSEAT_IP           XMODE=$XMODE               \
       START_POS=$START_POS         MAXSPD=$MAXSPD


nsplug meta_vehicle.bhv targ_$VNAME.bhv $NSFLAGS VNAME=$VNAME  \
       SPEED=$SPEED    ZONE=$ZONE

if [ ${JUST_MAKE} = "yes" ] ; then
    echo "Files assembled; nothing launched; exiting per request."
    exit 0
fi


#--------------------------------------------------------------
#  Part 6: Launch the processes
#--------------------------------------------------------------

echo "Launching $VNAME MOOS Community. WARP="$TIME_WARP
pAntler targ_${VNAME}.moos >& /dev/null &
echo "Done Launching $VNAME MOOS Community"

#---------------------------------------------------------------
#  Part 7: If launched from script, we're done, exit now
#---------------------------------------------------------------
if [ "${AUTO_LAUNCHED}" = "yes" ]; then
    exit 0
fi

#---------------------------------------------------------------
# Part 8: Launch uMAC until the mission is quit
#---------------------------------------------------------------
uMAC targ_$VNAME.moos
kill -- -$$
