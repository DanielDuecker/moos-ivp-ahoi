#!/bin/bash -e
#--------------------------------------------------------------
#   Script: blaunch.sh  (Batch Launch)
#   Author: Raymond Turrisi
#     Date: Sept. 19
#--------------------------------------------------------------

# Given a directory of configuration conditions, and a directory of parameter conditions, each set of parameters for each set of configurations K times. 
# i.e. k*(configuration_conditions * parameter_conditions)

# Initialize initial values for script

# Parse arguments

## Arguments being: 
# A generator function for configuration conditions
# An index or an index range for a set of configuration conditions, for use with a generator function
# A generator function for parameter conditions
# An index or an index range for a set of parameter conditions, for use with a generator function
# optionally: 
# - time warp
# - the number of trials for each pairing
# - whether or not a post processing script/job will be executed after each run
# i.e. ./blaunch.sh 10 --cc="config_set1.py" --cargs="[1..100]" --cp="param_set1.py" --pargs="[1..100]" --k=3 --pp="post_sequence.sh"
#   > batch launch at timewarp 10, with a generator function for configurations named config_set1.py, configuration function arguments 
#       (in this case, a range from indices 1 to 100), a parameter generator function named param_set1.py, with parameter configuration arguments, at 3 trials each, passing a post processing shell script

CONFIG_GENERATOR=""
CONFIG_RANGE=""
CONFIG_START=1
CONFIG_END=1
TIME_WARP=20
PARAM_GENERATOR=""
PARAM_RANGE=""
PARAM_START=1
PARAM_END=1
MISSION_TIME=600
#If a MOOS process is no longer reporting an uptime, in realtime, we track the process time to bring things down just in case
PROCESS_TIME=$(( 10 + $MISSION_TIME / $TIME_WARP))
TRIALS=1
POST_PROCESS_SCRIPT_PATH=""
LAUNCH_ARGS=""


#TODO: Allow multiple modes of launch, can provide steps for config and parameter ranges, or a file which has all the experiments to make up for, i.e. the failed directory
idx=0
while [[ idx -lt $# ]]; do
    idx=$((idx+1))
    ARGI=${!idx}
    CMD_ARGS+=" ${ARGI}"
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ]; then
	echo "Not yet!"
	exit 0;
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then 
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--cg" ]; then
        idx=$((idx+1))
        CONFIG_GENERATOR=${!idx}
    elif [ "${ARGI}" = "--pg" ]; then
        idx=$((idx+1))
        PARAM_GENERATOR=${!idx}
    elif [ "${ARGI}" = "--k" ]; then
        idx=$((idx+1))
        TRIALS=${!idx}
    elif [ "${ARGI:0:9}" = "--crange=" ]; then
        TERM="${ARGI#--crange=*}"
        TERM="${TERM//[\[\]]}"
        CONFIG_START="${TERM%%..*}"
        CONFIG_END="${TERM##*..}"
    elif [ "${ARGI:0:9}" = "--prange=" ]; then
        TERM="${ARGI#--prange=*}"
        TERM="${TERM//[\[\]]}"
        PARAM_START="${TERM%%..*}"
        PARAM_END="${TERM##*..}"
    elif [ "${ARGI}" = "--nogui" -o "${ARGI}" = "-n" ]; then
        LAUNCH_ARGS+=" $ARGI"
    else 
	echo "$ME: Bad Arg: $ARGI. Exit Code 1."
	exit 1
    fi
done

idx=0
p_pid=-1
t_start=$(date +%s)

# Open a blaunch log file, writing the mission index and the time
logname="logs/${t_start}.log"

# For each configuration index which was given
for i in $(seq $CONFIG_START $CONFIG_END); do

    # For each parameter index which was given
    for j in $(seq $PARAM_START $PARAM_END); do

        #For each trial which was asked
        for k in $(seq 1 $TRIALS); do
            #TODO: Write a task process which isolates this runtime logic within this block. (use xlaunch)
            # Ideally, it will run a mission, and if the mission times out, or some part fails
            # in post processing, it will try to run it once more before labeling it as a bad 
            # mission. The most common mode of failure has been when all the agents don't receive a correct ordering. 
            # When a mission fails, we want to zip it and see what happens

            #Run one trial

            # If we are running in the context of singularity, multiple containers are sharing this file system, so we put a mutex
            # on this element until this mission/test is off the ground

            #TODO: This is only for singularity containers, and isn't really the best solution. Need to improve this
            t_enter=$(date +%s)
            while [ -e "singularity.lock" ]; do
                echo "singularity.lock: Another container is launching this mission"
                t_now=$(date +%s)
                d=$((t_now-t_enter))

                sleep 0.5
            done

            #Put a lock on the directory until the mission is launched and all the files for this mission have been used
            touch singularity.lock
            #Generate a new configuration
            python3 $CONFIG_GENERATOR $i

            #Generate a new set of parameters
            python3 $PARAM_GENERATOR $j

            #Set timers
            mission_duration=0
            mission_start=$(date +%s)

            t_now=$(date +%s)
            duration=$((t_now-t_start))
            
            #Generate name of this mission, which is also used for the log files
            mission_name=$(printf "C%03d_P%05d_K%1d" $i $j $k)
            echo "${idx} | ${duration}: Running configuration ${i}, Parameter set ${j}, for trial ${k}"

            #Run the mission and detach, but capture the Process ID number
            ./launch.sh $LAUNCH_ARGS $TIME_WARP --mname=$mission_name &> /dev/null &
            pid_l=$!
            #This should be just slightly larger than the time it takes to bring up all the apps in pAntler - check time between launches
            sleep 2
            rm singularity.lock

            #Let things bring themselves up
            sleep 6

            #Start the mission by poking the DB
            MOOSTime=$(date +%s)
            MOOSTime=$(( $MOOSTime * 10 + 5))

            uPokeDB targ_shoreside.moos \
                              DEPLOY_ALL=true \
                MOOS_MANUAL_OVERRIDE_ALL=false \
                              LOITER_ALL=false \
                              RETURN_ALL=false \
                             STATION_ALL=false \
                       MISSION_TASK_ALL=type=waypoint,id=001,waypt_x=20,waypt_y=-20,task_time=@MOOSTime \
                VIEW_RANGE_PULSE=x=0,y=0,radius=50,duration=10,fill=0.9,label=nil, \
                      edge_color=white,fill_color=white,edge_size=1 \
                &> /dev/null &

            DONE="false"

            #State monitoring machine, sustaining checks before bringing the mission down
            while [ "${DONE}" = "false" ] ; do 
                echo "   Mission Running..."
                t_now=$(date +%s)
                mission_duration=$((t_now-mission_start))
                #1) Has the process time for this session ran over? This would imply a hanging process or application, if it has been exceeded, we cut it
                if [ $mission_duration -gt $PROCESS_TIME ] ; then
                    echo "   Process TimeOut" 
                    DONE="true"
                    break
                fi

                #2) Have we received a QUIT_MISSION queue
                if uQueryDB targ_shoreside.moos           \
                    --condition="QUIT_MISSION == true" --wait=2 >& /dev/null ; then 
                    echo "   Mission Complete" 
                    DONE="true"
                    break
                    #3) Have we been running over the allotted expected mission time?
                    elif uQueryDB targ_shoreside.moos         \
                        --condition="DB_UPTIME >= 600" --wait=2 >& /dev/null ; then 
                    echo "   Mission TimeOut" 
                    DONE="true"
                    break

                    else
                    sleep 5
                fi
                
            done
            sleep 1

            #Make sure every single process is brought down
            nuke_moos2 $pid_l &

            sleep 2 
            
            #TODO: Monitor this process to make sure it gets brought down, but still detach
            #TODO: would like to also monitor it and see if it fails, where if it is from a lack of data, we can rerun the mission
            ./post_process.sh $mission_name &
        
            #Get rid of all the targ files, and write the time to complete these cycle to the blaunch log
            #TODO: In singularity, with multiple containers, they see eachothers files. Can't remove the target files or files which may be shared among processes
            #rm targ_*
            t_now=$(date +%s)
            echo "$idx, $t_now" >> $logname
            sleep 2

            #Repeat! 
            idx=$((idx+1))
        done

    done

done

#Need to wait for the last post processor to finish
wait $!
