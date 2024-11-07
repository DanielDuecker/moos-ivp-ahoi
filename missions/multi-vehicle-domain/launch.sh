#!/bin/bash -e
#---------------------------------------------------------------
#   Script: launch.sh
#  Mission: alpha_seascout
#   Author: Mike Benjamin
#   LastEd: 2021-Jun-08
#---------------------------------------------------------------
#  Part 1: Set global var defaults
#---------------------------------------------------------------
vecho() { if [ "$VERBOSE" != "" ]; then echo "$ME: $1"; fi }

ME=`basename "$0"`
TIME_WARP=1
JUST_MAKE=""
VERBOSE=""
AUTO_LAUNCHED="no"
CMD_ARGS=""
NOGUI=""
NOCONFIRM="-nc"

RANDSTART="true"
SHORE_PSHARE="9200"
SHOREIP="localhost"
AMT=3

TRANSIT_SPD=0.5
MAXIMUM_SPD=2.0

VLAUNCH_ARGS=" --auto "
SLAUNCH_ARGS=" --auto "

#---------------------------------------------------------------
#  Part 2: Check for and handle command-line arguments
#---------------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "$ME [SWITCHES] [time_warp]                                 "
	echo "  --help, -h         Show this help message                "
	echo "  --just_make, -j    Just make targ files, no launch       "
	echo "  --verbose, -v      Verbose output, confirm before launch "
	exit 0
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--just_make" -o "${ARGI}" = "-j" ]; then
        JUST_MAKE="-j"
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ]; then
        VERBOSE="--verbose"
    elif [ "${ARGI}" = "--norand" -o "${ARGI}" = "-r" ]; then
        RANDSTART="false"
    elif [ "${ARGI:0:9}" = "--maxspd=" ]; then
        VLAUNCH_ARGS=" $ARGI"
    elif [ "${ARGI:0:6}" = "--amt=" ]; then
        AMT="${ARGI#--amt=*}"
    else
        echo "$ME: Bad arg:" $ARGI "Exit Code 1."
        exit 1
    fi
done
echo "After parse"

#-------------------------------------------------------------
# Part 5: Generate random starting positions, speeds and vnames
#-------------------------------------------------------------
vecho "Picking Convoy vehicle starting positions."

if [ "${RANDSTART}" = "true" -o  ! -f "vpositions.txt" ]; then
    ./pickpos.sh $AMT
fi

# vehicle names and colors are always deterministic
pickpos --amt=$AMT --vnames=abe,ben,cal,deb,eve,fin,ned,max,oak  > vnames.txt
pickpos --amt=$AMT --colors  > vcolors.txt

VEHPOS=(`cat vpositions.txt`)
VNAMES=(`cat vnames.txt`)
COLORS=(`cat vcolors.txt`)

echo "VEHPOS length: ${#VEHPOS[@]}"
echo "VNAMES length: ${#VNAMES[@]}"
echo "COLORS length: ${#COLORS[@]}"

#---------------------------------------------------------------
#  Part 3: Initialize and Launch the vehicles
#---------------------------------------------------------------

echo "Before loop"
# print index and amt
VLAUNCH_ARGS+=" $NOCONFIRM "
ALL_VNAMES=""
for INDEX in `seq 1 $AMT`;
do
    echo "Index: $INDEX"
    echo "Amt: $AMT"
    sleep 0.2
    echo "Array Index: $INDEX"
    ARRAY_INDEX=$((INDEX - 1))
    echo "Array Index: $ARRAY_INDEX"
    START=${VEHPOS[$ARRAY_INDEX]}
    VNAME=${VNAMES[$ARRAY_INDEX]}
    COLOR=${COLORS[$ARRAY_INDEX]}
    echo "Start: $START"

    if [ "${ALL_VNAMES}" != "" ]; then
	ALL_VNAMES+=":"
    fi
    ALL_VNAMES+=$VNAME
    
    VLAUNCH_ARGS+=" $NOCONFIRM "
    IX_VLAUNCH_ARGS=$VLAUNCH_ARGS
    IX_VLAUNCH_ARGS+=" --index=$INDEX --start=$START    "
    IX_VLAUNCH_ARGS+=" --maxspd=$MAXIMUM_SPD            "
    IX_VLAUNCH_ARGS+=" --speed=$TRANSIT_SPD             " 
    IX_VLAUNCH_ARGS+=" --color=$COLOR  --sim            " 
    IX_VLAUNCH_ARGS+=" --vname=$VNAME  --shore=$SHOREIP "
    IX_VLAUNCH_ARGS+=" $VERBOSE $CONVOY_VERS $MEDIATED  "
    IX_VLAUNCH_ARGS+=" $TIME_WARP "

    echo "Before launch"
	./launch_heron.sh $IX_VLAUNCH_ARGS	
    echo "After launch"
done
# Launch spurdog - sim mode
#---------------------------------------------------------------
#  Part 4: Launch the shoreside
#---------------------------------------------------------------
echo "$ME: Launching Shoreside ..."
./launch_shoreside.sh --auto $VERBOSE $JUST_MAKE $TIME_WARP

#---------------------------------------------------------------
# Part 5: Launch uMAC until the mission is quit
#---------------------------------------------------------------
uMAC targ_shoreside.moos
kill -- -$$

