---------------------------------------------------------------------
Fname: README.md
Author: Raymond Turrisi
LastEd: October 2024

This is a template mission for the vehicles, outlined specifically on
the herons, and is the standard used on the Spurdog. I am primarily 
creating this so I can duplicate this mission for other tests more 
easily, without carrying baggage across missions, but others may find
it useful. 

It consists of an example organized mission structure which improves 
portability between missions, and a pipeline for analyzing data, and 
producing plots. 

How would you use this?
    1) (optional) Install a virtual environment with python
        Ubuntu: sudo apt install python3-venv
        Mac: <Install python3>
    2) alpha_heron/
        python3 -m venv venv 
    3) pip3 install -r info/requirements.txt
    4) ./launch.sh 20
    5) ./post_process.sh logs/<MISSION_HASH>

Usage: 

./launch.sh 20
    > Runs a single heron in simulation at a timewarp of 20

./post_process.sh logs/<MISSION_HASH>
    > Thins and cleans all node log directories
    > Uses mdm to extract data from all the nodes and bundles the 
        data into JSON files, or CSV files for every variable
    > Produces a plot of the mission, by default, at the sailing 
        pavilion, performing a reversed geodesic conversion for 
        NAV_X/NAV_Y, in order to reduce dependencies on strictly 
        running on a physical vehicle with GPS. This is only for
        illustrative purposes in building out these tools. 
    > Results in: 
        logs/<MISSION_HASH>/
            data_mdm/
                LOG_VEHICLE*/
                    log_vehicle*_alog_csvs/
                        *.csv
                        ...
                        ...
                    log_vehicle*.json
                LOG_SHORESIDE*/
                    log_shoreside*_alog_csvs/
                        *.csv
                        ...
                        ...
                    log_shoreside*.json
                *mission_data_whole.json
            LOG_VEHICLE*/
                LOG_VEHICLE*.alog
                LOG_VEHICLE*._moos
                targ_vehicle._bhv
            LOG_SHORESIDE*/
                LOG_SHORESIDE*._moos
                LOG_SHORESIDE*.alog
            meta/
                mission_trajectory.png

Other: 

lock_logs: produces a hidden file which changes the behavior of 
    clean.sh, so that if the hidden file is present, it asks for 
    confirmation before deleting the logs

mdm/ : a directory which contains wrappers and supporting 
    configuration files for mdm. It is configured for each 
    mission typically

plugs/ : a directory outlining all the plug files for agents, 
    shoreside, and standard behaviors and variables. The 
    actual mission and desired behaviors are included in the
    meta_vehicle.bhv file

info/ : a directory containing mission related information 
    and documentation, including any requirements for 
    analyzing data in python. Assume that you may be using a 
    virtual environment

targs/ : The directory where all the target files go and are 
    referenced

{venv}/ : not present in the upload, but may be included in 
    a specific mission should you use python like this. 
    i.e. 
        python3 -m venv venv 
    May also include the requirements for analyzing the data, including 
    what is used in this template/demonstration. 
    i.e. 
        pip3 install -r info/requirements.txt