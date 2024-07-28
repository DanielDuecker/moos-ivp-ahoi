#!/bin/bash 

VERBOSE=""

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
	printf "%s [SWITCHES]                       \n" $0
	printf "  --verbose                         \n" 
	printf "  --help, -h                        \n" 
	exit 0;	
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ] ; then
	VERBOSE="-v"
    else 
	printf "Bad Argument: %s \n" $ARGI
	exit 0
    fi
done

#-------------------------------------------------------
#  Part 2: Do the cleaning!
#-------------------------------------------------------

ans="y"
if [[ -f ".loglock" ]]; then 
	read -p "Are you sure you want to clear log files? [y/n]: " ans
fi 

case $ans in
	[yY]* )
		rm -rf  $VERBOSE   logs/L* logs/C* logs/*-*-* logs/*.log logs/failed.txt logs/failed/*
		rm -f   $VERBOSE   *~  targ_* *.moos++ *.dbg debug_*.txt
		rm -f   $VERBOSE   .LastOpenedMOOSLogDirectory .mem_info_phelm*
		rm -f   $VERBOSE   vnames*.txt vspeeds.txt vpositions*.txt vcolors.txt
		;;
	[nN]* ) 
		echo "Exiting without deleting files"
		;;
esac 
