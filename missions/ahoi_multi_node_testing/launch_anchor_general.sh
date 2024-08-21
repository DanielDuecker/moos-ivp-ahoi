#!/bin/bash


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
	echo "  --vname=<abe>                                  " 
	echo "    Name of the vehicle being launched           " 
	echo "  --index=<1>                                    " 
	echo "    Index for setting MOOSDB and pShare ports    "
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
    # elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then 
    #     TIME_WARP=$ARGI
    # elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
	# JUST_MAKE="yes"
    # elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
    #     VERBOSE="yes"
    # elif [ "${ARGI}" = "--noconfirm" -o "${ARGI}" = "-nc" ]; then
	# CONFIRM="no"
    # elif [ "${ARGI}" = "--nomediate" -o "${ARGI}" = "-nm" ]; then
	# MEDIATED="no"
    # elif [ "${ARGI}" = "--auto" -o "${ARGI}" = "-a" ]; then
    #     AUTO_LAUNCHED="yes"
    # elif [ "${ARGI}" = "--logclean" -o "${ARGI}" = "-l" ]; then
	# LOG_CLEAN="yes"
    # elif [ "${ARGI}" = "--mtasc" -o "${ARGI}" = "-m" ]; then
	# MTASC="yes"

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
	
    # elif [ "${ARGI:0:5}" = "--ip=" ]; then
    #     IP_ADDR="${ARGI#--ip=*}"
    # elif [ "${ARGI:0:7}" = "--mport" ]; then
	# MOOS_PORT="${ARGI#--mport=*}"
    # elif [ "${ARGI:0:9}" = "--pshare=" ]; then
    #     PSHARE_PORT="${ARGI#--pshare=*}"
    # elif [ "${ARGI:0:8}" = "--shore=" ]; then
    #     SHORE_IP="${ARGI#--shore=*}"
    # elif [ "${ARGI:0:15}" = "--shore_pshare=" ]; then
    #     SHORE_PSHARE="${ARGI#--shore_pshare=*}"
    # elif [ "${ARGI:0:8}" = "--mname=" ]; then
    #     MISSION_NAME="${ARGI#--mname=*}"
    elif [ "${ARGI:0:8}" = "--vname=" ]; then
        VNAME="${ARGI#--vname=*}"
    # elif [ "${ARGI:0:8}" = "--color=" ]; then
    #     COLOR="${ARGI#--color=*}"
    # elif [ "${ARGI:0:8}" = "--index=" ]; then
    #     INDEX="${ARGI#--index=*}"
    # elif [ "${ARGI:0:8}" = "--start=" ]; then
    #     START_POS="${ARGI#--start=*}"
    # elif [ "${ARGI:0:8}" = "--speed=" ]; then
    #     TRANSIT_SPD="${ARGI#--speed=*}"
    # elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
    #     MAXIMUM_SPD="${ARGI#--maxspd=*}"
    # elif [ "${ARGI:0:7}" = "--tbhv=" ]; then
    #     TASKBHV="${ARGI#--tbhv=*}"
    # elif [ "${ARGI:0:5}" = "--cp=" ]; then
    #     CONVOY_POLICY="${ARGI#--cp=*}"

    # elif [ "${ARGI}" = "--active_convoy" -o "${ARGI}" = "-ac" ]; then
	# CONVOY_VERS="active"

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
    # if [ "${MTASC}" = "yes" ]; then
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

#pAntler ahoi_modem_static.moos --> start this separately =/

# Get the directory of the bash script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the arguments relative to the script directory
# SERVER_HOST="localhost"
# SERVER_PORT="9000"

SERVER_HOST= $IP_ADDR
SERVER_PORT= $MOOS_PORT

MODEM_CONFIG_FILE="$SCRIPT_DIR/local_modem_config.json"
ENVIRO_CONFIG_FILE="$SCRIPT_DIR/enviro_config.json"

# Define the path to the Python script
PYTHON_SCRIPT="$SCRIPT_DIR/../../src/pAhoiModemManager/pyAhoi_Anchor_Manager.py"

# Construct the command with optional flags based on the values
python3 "$PYTHON_SCRIPT" \
    --server_host $SERVER_HOST \
    --server_port $SERVER_PORT \
    --modem_config_file $MODEM_CONFIG_FILE \
    --enviro_config_file $ENVIRO_CONFIG_FILE

