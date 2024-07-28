#!/bin/python3
"""
   ___                _           ___                       
  / _ \__ _ _ __   __| | __ _    / _ \_____      _____ _ __ 
 / /_)/ _` | '_ \ / _` |/ _` |  / /_)/ _ \ \ /\ / / _ \ '__|
/ ___/ (_| | | | | (_| | (_| | / ___/ (_) \ V  V /  __/ |   
\/    \__,_|_| |_|\__,_|\__,_| \/    \___/ \_/\_/ \___|_|   
                                                            

We are assuming the use of MWDataMgr, which caches a collection of directories as a JSON, optionally, but preferred for this type of application
We take the top level JSON file which would appear, which possesses all the relevant data for a mission


TODO:
 - [ ] Have found semantically incorrect bids in which both agents win the exclusive auction, how do we handle cases in which we can learn from this?

"""



###### <START>
if __name__ == "__main__":
    import sys
    import os
    import json 
    import glob
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.pyplot
    
    import numpy as np
    import pandas as pd
    from matplotlib.path import Path
    import warnings
    warnings.filterwarnings("ignore") #matplotlib and pandas are too verbose

    ###### <SETUP>
    mission_directory = sys.argv[1]
    mission_hash = mission_directory.split("/")[-1]
    glb = glob.glob(f"{mission_directory}_tmp/*.json")
    fname = glb[0]
    output_directory = f"{mission_directory}_meta/"
    try:
        os.mkdir(output_directory)
    except OSError:
        pass 
        #print(f"Creation of the directory {path} failed")
    #TODO: Update color mapping to account for 26 agents?
    color_mapping = {"yellow":"y",
                     "red":"r",
                     "green":"g",
                     "purple":"m",
                     "dodger_blue":"b"}
    
    ##### Open all the configuration and data files we need to obtain preceding information
    #Load the JSON file
    mission_data = json.load(open(fname))

    ###### </SETUP>

    ###### <EXTRACTING DATA>
    #Get waypoints from our standard circuit file
    circuit_file = "plug_circuit.moos"
    with open(circuit_file, 'r') as f:
        circuit = f.read()
        circuit = circuit.replace(" ","")
        idx = circuit.find("=")
        circuit = circuit[idx+1:]
        circuit = circuit.split(":")
        split_point = lambda point: [float(v) for v in point.split(',')]
        circuit = [split_point(point) for point in circuit]

    # For stability proxy 1: Obtain the necessary turns in order to complete a circuit
    circuit_turns = 0
    first_leg_angle = 0
    for idx in range(2,len(circuit)):
        p_1 = circuit[idx-2]
        p_2 = circuit[idx-1]
        p_3 = circuit[idx]
        
        leg1_angle = np.arctan2(p_2[1]-p_1[1],p_2[0]-p_1[0])*180/np.pi
        leg2_angle = np.arctan2(p_3[1]-p_2[1],p_3[0]-p_2[0])*180/np.pi

        #Assume the agent took the shortest closure distance
        turn_angle = (leg2_angle-leg1_angle+180)%360 - 180
        if(idx == 2):
            first_leg_angle = turn_angle        
        circuit_turns+=abs(turn_angle)

    legend_markers = ["Waypoints"]

    #For all the participants in this mission, extract the data we would like for our analysis
    agent_names = []
    agent_info = dict()
    all_general_info = dict()
    agent_start_pos = []
    agent_distances = []

    #Get the parameters we are varying from configuration file
    variable_file_1 = "plug_bhv_variables.moos"
    agent_variables = dict()
    stripped_chars = [" ","\n","\r","\t"]
    with open(variable_file_1, 'r') as f:
        while(True):    
            line = f.readline()
            if line == "":
                break 
            else: 
                #Strip all comments out of the line, i.e. everything to the right of a //
                idx = line.find("//")
                if idx != -1:
                    line = line[0:idx]
                    if len(line) == 0:
                        continue
                for c in stripped_chars:
                    line = line.replace(c,"")
                line = line.split("=")
                agent_variables[line[0]] = line[1]    

    ## 1) Extracts all the data from the JSON file, while converting data to the write type
    ## 2) Data is stored into a list for now, unsynchronized, and is later time synchronized

    all_agent_data = []
    shoreside_data = pd.DataFrame()
    node_report_col_names = ["TIME","X","Y","HDG","SPD"]
    node_report_types = ["f","f","f","f","f"]

    all_vars = []
    all_vars.extend(node_report_col_names)
    all_vars = [f.lower() for f in all_vars]
    all_var_types = []
    all_var_types.extend(node_report_types)

    type_mapping = dict(zip(all_vars,all_var_types))

    def cast(var,dat):
        var = var.lower()
        if(var == "f" or type_mapping[var] == "f"):
            return float(dat)
        elif(var == "i" or type_mapping[var] == "i"):
            return int(dat)
        elif(var == "s" or type_mapping[var] == "s"):
            return str(dat)
        
    #Extract all the data we care about from the JSON file
    for key, val in mission_data.items():
        if(key.find("SHORESIDE") > 0):
            #Collect near collision information
            data = val["data"]
            ct = "COLLISION_TOTAL"
            pre_df_tc = [[i[0], float(i[1])] for i in data[ct]]
            #incrementing_total_near_misses = data["NEAR_MISS_TOTAL"] #A list of [time, data[dict_keys], source]
            nm = "NEAR_MISS_TOTAL"
            pre_df_nm = [[i[0], float(i[1])] for i in data[nm]]

            ss_df1 = pd.DataFrame(pre_df_tc,columns=["time", "collision_total"]).set_index("time")
            ss_df2 = pd.DataFrame(pre_df_nm,columns=["time", "near_miss_total"]).set_index("time")

            ss_group = [ss_df1,ss_df2]
            
            shoreside_data = ss_group.pop()

            for s in ss_group:
                shoreside_data = shoreside_data.join(s,how="outer")
        else:
            #For each agent, we are going to capture all information we are interested in
            agent_name = key
            agent_name = agent_name.replace("LOG_","")
            idx = agent_name.find("_")
            agent_name = agent_name[0:idx].lower()
            legend_markers.append(agent_name)
            agent_names.append(agent_name)
            data = val["data"]

            #Get all the data we care about from node reports
            node_reports = data["NODE_REPORT_LOCAL"]

            #Prepends the agent name to the node report name, makes it lower case to be consistent
            # further, time will be the same
            col_names = [f"{agent_name}_{t}".lower() if t != "TIME" else t.lower() for t in node_report_col_names]

            #Unpacks the data we want from the node report
            nr_agent_pre_df = [[cast(n,v[1][n]) for n in node_report_col_names] for v in node_reports]

            #Occasional issues in which DESIRED_RUDDER and DESIRED_THRUST nondeterministically exist, temporary fix until a real solution is found
            if "DESIRED_RUDDER" in data.keys():
                rddr = [[entry[0],cast("f",entry[1])] for entry in data["DESIRED_RUDDER"]]
            else:
                rddr = [[entry[0],0] for entry in data["NODE_REPORT_LOCAL"]]
            rddr_df = pd.DataFrame(rddr, columns=["time", f"{agent_name}_rudder"]).set_index("time")
            if "DESIRED_THRUST" in data.keys():
                thrust = [[entry[0],cast("f",entry[1])] for entry in data["DESIRED_THRUST"]]
            else:
                thrust = [[entry[0],0] for entry in data["NODE_REPORT_LOCAL"]]
            thrust_df = pd.DataFrame(thrust, columns=["time", f"{agent_name}_thrust"]).set_index("time")


            #Puts all the data now in the collection of dataframes still awaiting to be merged
            agent_df = pd.DataFrame(nr_agent_pre_df,columns=col_names).set_index("time")

            agent_df = agent_df.join(rddr_df,how='outer')
            agent_df = agent_df.join(thrust_df,how='outer')
    
            #We assume ZOH, in the sense that a message to the MOOSDB is the start of a new state
            # fill forward
            #agent_df.fillna(method='ffill',inplace=True)

            #All NaNs that remain, is in the very start of the mission when agents are being brought online, such that 
            # no data exists to be filled forward (drop it)
            #agent_df.dropna(inplace=True)

            all_agent_data.append(agent_df.copy())

            slower_rng = 0
            ideal_rng = 0
            faster_rng = 0
            full_lag_rng = 0
            following = "na"
            #TODO: Extract agents convoy/speed policy
            if "CONVOY_SPD_POLICY" in data:
                is_leader = False
            else:
                is_leader = True
                all_general_info["leader"] = agent_name

            if is_leader:
                pass
            else:
                spd_policy_str = data["CONVOY_SPD_POLICY"][0][1]
                all_items = spd_policy_str.split("|")
                all_items = [k.split("=") for k in all_items]
                spd_policy = dict(all_items)
                slower_rng = float(spd_policy["slower_rng"])
                ideal_rng = float(spd_policy["ideal_rng"])
                faster_rng = float(spd_policy["faster_rng"])
                full_lag_rng = float(spd_policy["full_lag_rng"])

                task_convoy = data["TASK_WON"][-2][1]

                all_items = dict([k.split("=") for k in task_convoy.split("|")])
                following = all_items["id"]
                following = following.replace("follow_","")


            color = color_mapping[node_reports[0][1]["COLOR"]]

            agent_info[agent_name] = {"slower_rng":slower_rng,
                                      "ideal_rng":ideal_rng,
                                        "faster_rng":faster_rng,
                                        "color":color,
                                        "is_leader":is_leader,
                                        "following":following}
    
    

    
    # Find a leader, then find who's following the leader, then them, etc..
    # TODO: Check the semantics of this once more
    # TODO: Found an edge case in which multiple agents win the same bid
    lead = all_general_info["leader"]
    all_general_info["ordering"] = {lead:1}
    idx = 2
    found = [lead]

    for idx in range(2,len(agent_names)):
        for name_1, v1 in agent_info.items():
            if name_1 in found:
                continue 
            else:
                #Find who is following this lead
                
                if v1['following'] == lead:
                    all_general_info["ordering"].update({name_1:idx})
                    found.append(name_1)
                    lead = name_1
                    break

    #Nobody is following the last agent, so we need to infer their order
    tail = [names for names in agent_names if names not in found]
    all_general_info["ordering"].update({tail[0]:idx+1})

    ### Join and time synchronize all of the data

    all_data_df = shoreside_data.copy()

    #Joins the dataframes with as best ordered rows as pandas can
    #   i.e. the time in this case is monotonically increasing, non-overlapping
    #   timestamps are filled with NaN for the dataset which doesn't have it

    for df in all_agent_data:
        all_data_df = all_data_df.join(df,how='outer')
    
    #We assume ZOH, in the sense that a message to the MOOSDB is the start of a new state
    # fill forward
    all_data_df.fillna(method='ffill',inplace=True)

    #All NaNs that remain, is in the very start of the mission when agents are being brought online, such that 
    # no data exists to be filled forward (drop it)
    all_data_df.dropna(inplace=True)

    #Check to make sure all time rows are monotonically increasing

    #TODO: Add the time differences as its own column
    all_data_df = all_data_df.sort_index()
     #all_data_df.sort_values(all_data_df.index, axis=0)
    
    #Base everything w/rt mission start
    tbegin = all_data_df.index[0]
    all_data_df.index = all_data_df.index - tbegin
    t_diff = pd.DataFrame(all_data_df.index).diff().set_index(all_data_df.index)
    all_data_df.dropna(inplace=True) #We only care about what happens when all agents are connected

    #At this point, all the logs are time synchronized, and we can more easily draw relational conclusions among the agents
    ###### </EXTRACTING DATA>

    ###### <ANALYZING DATA>

    # Not really analysis, but update the legend markers for the main thumbnail to include the name and order
    for idx,name in enumerate(legend_markers):
        if idx == 0:
            continue
        else:
            #TODO: Check this for occasional errors
            try:
                legend_markers[idx]=f"{name}_{all_general_info['ordering'][name]}"
            except:
                print("had an issue with this command")
                print(all_general_info['ordering'])
                legend_markers[idx]=f"{name}_{all_general_info['ordering'][name]}"

                exit(1)

    #For each follower agent, we are going to look at who they are supposed to be following, and track their distance
    for n in agent_names:
        if n == all_general_info["leader"]:
            continue
        following = agent_info[n]["following"]
        
        rng = all_data_df[[f"{n}_x",
                             f"{n}_y",
                             f"{following}_x",
                             f"{following}_y"]]
        
        rng["dist"] = np.sqrt(np.power(rng[f"{n}_x"]-rng[f"{following}_x"],2)+np.power(rng[f"{n}_y"]-rng[f"{following}_y"],2))
        all_data_df[f"{n}_trgt_rng"] = rng["dist"] #Target Range
        all_data_df[f"{n}_in_rng"] = (rng["dist"] < agent_info[n]["faster_rng"]) & (rng["dist"] > agent_info[n]["slower_rng"]) # In Convoy Range
        all_data_df[f"{n}_rng_dev"] = rng["dist"] - agent_info[n]["ideal_rng"] # Agents deviation from desired range

        #Capture whether or not an agent is entering or exiting convoy range
        all_data_df[f"{n}_entered_convoy"] = all_data_df[f"{n}_in_rng"].astype(int).diff()
    
    #Now that we have all the agents ranging information to the target, identify the times in which all the agents are in range (in the intended convoy)
    all_data_df[f"all_in_range"] = True
    for n in agent_names:
        if n == all_general_info["leader"]:
            continue
        all_data_df[f"all_in_range"] &= all_data_df[f"{n}_in_rng"]

    #We have whether or not all the agents are now in range of their desired convoy, now we can identify when they transition in and out of convoying
    # Assume these conditions are integers, mask the transitions such that 1 0 0 0 1 means it is in convoy, leaves convoy, reenters convoy
    # Now the derivative provides flags [na -1 0 0 1], where we can now identify exactly when it enters a convoy, rather than just that it
    # is in a convoy
    # i.e. we can count how many times it entered and exited a convoy (should be fairly redundant)
    all_data_df[f"all_in_range_transition"] = all_data_df[f"all_in_range"].astype(int).diff()

    #Find out the point to point distances for each agent and the total odometry of the agent
    # Divide the point to point distance total odometry 
    agent_straightnesses = dict()
    
    # Observe the necessary turns and distance an agent would have had to do to complete the circuit
    # Divide the necessary turns by the actual turns
    agent_turninesses = dict()

    for n in agent_names:
        hdgs = all_data_df[f"{n}_hdg"].to_numpy()
        x_start = all_data_df[f"{n}_x"].iloc[0]
        y_start = all_data_df[f"{n}_x"].iloc[0]
        hdg_start = hdgs[0]
        
        x_diffs = all_data_df[f"{n}_x"].diff().to_numpy()[1:]
        y_diffs = all_data_df[f"{n}_y"].diff().to_numpy()[1:]

        odometry = 0
        for idx in range(1,len(x_diffs)):
            odometry+=np.linalg.norm([x_diffs[idx]-x_diffs[idx-1],y_diffs[idx]-y_diffs[idx-1]])

        agent_distances.append(odometry)

        start_pos = [x_start,y_start]
        
        agent_circuit = [start_pos]
        agent_circuit.extend(circuit)

        agent_required_turns = []
        point_to_point_dist = 0

        # Required turning distance from the agents initial point and heading
        necessary_turniness = abs((first_leg_angle-hdg_start + 180)%360 - 180) 
        # Add the absolute required of turns for the total circuit
        necessary_turniness+=circuit_turns
        for idx in range(1,len(agent_circuit)):
            p2p = np.sqrt((agent_circuit[idx][0]-agent_circuit[idx-1][0])**2+(agent_circuit[idx][1]-agent_circuit[idx-1][1])**2)
            point_to_point_dist+=p2p
        
        # Stability Proxy 1: Straightness - How must unnecessary distance does the agent cover? This would characterize its efficiency, where 1 is best
        agent_straightness=point_to_point_dist/odometry
        agent_straightnesses[n] = agent_straightness

        # Stability Proxy 2: "Turny-ness" - does the agent oscillate, i.e. turn more than what is strictly necessary?. 1 is best (likely unachievable)
        agent_turniness =  np.sum(abs(((np.diff(hdgs)+180)%360 - 180)))
        agent_turninesses[n] = necessary_turniness/agent_turniness

    #These measures should be highly correlated, and essentially redundant measures
    straightness_index = np.mean([v for _,v in agent_straightnesses.items()]) #Batshelet, Benhamou?
    turn_index = np.mean([v for _,v in agent_turninesses.items()])

    ###### </ANALYZING DATA>

    ###### <PLOT ALL THE DATA>

    ###### <Main high level thumbnail plot>
    ##### Compose summarization plot for mission
    #Instantiage a plot, optionally lod the MIT sailing pavilion
    fig_tn = plt.figure()
    fig_tn.set_figheight(6)
    fig_tn.set_figwidth(6)

    #All agents thumbnail
    ax1_tn = plt.subplot2grid(shape=(4,4),loc=(0,0),rowspan=4,colspan=4)

    #Text summary
    #ax2_tn = plt.subplot2grid(shape=(4,2),loc=(3,0),rowspan=1,colspan=1)    

    #img = plt.imread("/Users/raymondturrisi/svn/moos-ivp/ivp/data/MIT_SP.tif")
    #ax.imshow(img,extent=[-550, 600, -494, 215])

    
    #Plot the target waypoints
    ax1_tn.plot([x for x,y in circuit], [y for x,y in circuit], 
            marker='x',
            markersize=10,
            markeredgewidth=5,
            markerfacecolor="y",
            markeredgecolor="darkorange",
            linestyle='None')

    #Plot the master thumbnail for the mission
    for idx, n in enumerate(agent_names):
        if agent_info[n]["is_leader"]:
            ax1_tn.plot(all_data_df[f"{n}_x"],all_data_df[f"{n}_y"],
                    agent_info[n]["color"],
                    linestyle=":",
                    zorder= 20,
                    linewidth=4)
        else:
            ax1_tn.plot(all_data_df[f"{n}_x"],all_data_df[f"{n}_y"],
                    agent_info[n]["color"],
                    linestyle="-")
            
    vertices = [(0, 0), (-1, 1), (1, 1), (2, 0), (1, -1), (-1, -1), (0, 0)]
    codes = [1,2,2,2,2,2,79]
    p = Path(vertices,codes)

    for idx, n in enumerate(agent_names):
        hdgs = all_data_df[f"{n}_hdg"].to_numpy()
        hdg_start = hdgs[0]
        #hdg_start = all_data_df[f"{n}_hdg"][0].iloc[0]
        x_start = all_data_df[f"{n}_x"][0]
        y_start = all_data_df[f"{n}_y"][0]
        m = matplotlib.markers.MarkerStyle(p)
        m._transform = m.get_transform().rotate_deg(hdg_start)
        color = agent_info[n]["color"]
        ax1_tn.scatter(x_start,y_start,marker=m,s=150,c=color,zorder=100)
    
    ax1_tn.set_aspect('equal',adjustable='box')
    ax1_tn.set_title(f"Mission <{mission_directory}>")
    ax1_tn.grid(True)
    ax1_tn.set_xlabel("Easting (m)")
    ax1_tn.set_ylabel("Northing (m)")
    ax1_tn.legend(legend_markers,ncols=2,borderpad=0)
    
    #Now we add a little summary within the plot
    collisions = all_data_df['collision_total'].iloc[-1]
    scores=f"collisions={collisions:0.0f}"
    near_misses = all_data_df['near_miss_total'].iloc[-1]
    scores+=f", near_misses={near_misses:0.0f}"
    scores+=f",\nsi={straightness_index:0.2f}"
    scores+=f", ti={turn_index:0.2f}"
    #ax2_tn.axis("off")
    #ax2_tn.set_xlim([0, 200])
    #ax2_tn.set_ylim([0, 100])
    #ax2_tn.text(-10,80,scores,ha="left",va="top",fontsize=8,wrap=True)
    fig_tn.canvas.draw_idle()
    
    plt.savefig(f"{output_directory}{mission_hash}_tn.png", dpi=80)
    plt.close()
    ###### </Main high level thumbnail plot>

    ###### <Detailed analysis driven plot>
    fig_det = plt.figure()
    fig_det.set_figheight(8)
    fig_det.set_figwidth(7)

    ### Left hand side
    #Leader's track w/rt to time
    ax_leader_det = plt.subplot2grid(shape=(6,2),loc=(0,0),rowspan=2,colspan=1)

    #Near misses/collisions w/rt time
    ax_nm_and_cols_det = plt.subplot2grid(shape=(6,2),loc=(3,0),rowspan=1,colspan=1)

    #Plot a histogram of the agents name/order and the total time they spent in a convoy
    ax_perc_in_convoy_det = plt.subplot2grid(shape=(6,2),loc=(4,0),rowspan=1,colspan=1)

    ### Right hand side (all time sync'd)
    #Heading differences for all agents (communicate lag and stability roughly) w/rt time
    ax_heading_det = plt.subplot2grid(shape=(6,2),loc=(0,1),rowspan=1,colspan=1)

    #Plot desired rudder
    ax_rudder_det = plt.subplot2grid(shape=(6,2),loc=(1,1),rowspan=1,colspan=1)

    #Speed differences for all agents (communicate lag and stability roughly) w/rt time
    ax_spd_chngs_det = plt.subplot2grid(shape=(6,2),loc=(2,1),rowspan=1,colspan=1)

    #Plot desired thrust
    ax_thrust_det = plt.subplot2grid(shape=(6,2),loc=(3,1),rowspan=1,colspan=1)

    #Range to target
    ax_rng_to_trg_det = plt.subplot2grid(shape=(6,2),loc=(4,1),rowspan=1,colspan=1)

    #Plot horizontal bands for the times in which all the agents are in a convoy
    ax_in_convoy_det = plt.subplot2grid(shape=(6,2),loc=(5,1),rowspan=1,colspan=1)

    
    #Plot the leaders trajectory w/rt to time and the times in which the collection of systems is in a convoy
    ln = all_general_info["leader"]
    leader_x = all_data_df[f"{ln}_x"]
    leader_y = all_data_df[f"{ln}_y"]
    sc = ax_leader_det.scatter(leader_x,leader_y,c=all_data_df.index,s=0.5)
    cbar = plt.colorbar(sc)
    cbar.ax.tick_params(labelsize=6)
    ax_leader_det.set_aspect('equal',adjustable='box')
    ax_leader_det.set_xlabel("Easting (m)")
    ax_leader_det.set_ylabel("Northing (m)")
    
    #get the indices in which all the agents are in a successful convoy
    team_convoying = (all_data_df["all_in_range"] == True)
    good_convoy_x = leader_x[team_convoying]
    good_convoy_y = leader_y[team_convoying]
    ax_leader_det.plot(good_convoy_x, good_convoy_y,
                    linestyle="None",
                    marker='o',
                    markersize=3,
                    markeredgecolor="darkorange",
                    markerfacecolor='g')
    
    ax_leader_det.grid(True)

    #Now we plot the differences in headings and speeds for each agent
    t = all_data_df.index
    legend = []
    speed_changes = []
    for n in agent_names:
        #While this next part looks highly redundant, it isn't and it makes for much nicer plots
        hdg_diffs = ((all_data_df[f"{n}_hdg"].diff()+180)%360 - 180)
        hdg_chngs_with_t = hdg_diffs.cumsum()
        spd = (all_data_df[f"{n}_spd"])
        speed_changes.append(np.abs(spd.diff()).sum())
        ax_heading_det.plot(t,hdg_chngs_with_t,linestyle=":",marker=".",markersize=0.5)
        ax_spd_chngs_det.plot(t,spd,linestyle=":",marker=".",markersize=0.5)
        legend.append(all_general_info["ordering"][n])

    mean_speed_changes=np.mean(speed_changes)
    ax_heading_det.legend(legend,
                          ncol=1,
                          fontsize=6,
                          borderpad=0,
                          labelspacing=0,
                          loc = 'center left',
                          bbox_to_anchor=(1,0.5))
    ax_heading_det.grid(True)
    ax_heading_det.set_title("Cummulative changes in degrees",fontsize=6)
    ax_heading_det.set_yticklabels(ax_heading_det.get_yticklabels(),fontsize=6)
    ax_spd_chngs_det.legend(legend,
                            ncol=1,
                            fontsize=6,
                            borderpad=0,
                            labelspacing=0,
                            loc = 'center left',
                            bbox_to_anchor=(1,0.5))
    ax_spd_chngs_det.grid(True)
    ax_spd_chngs_det.set_title("Cummulative changes in speed (m/s)",fontsize=6)
    ax_spd_chngs_det.set_yticklabels(ax_spd_chngs_det.get_yticklabels(),fontsize=6)

    legend = []
    for n in agent_names:
        if n == all_general_info["leader"]:
            continue 
        dist_to_target = all_data_df[f"{n}_trgt_rng"]
        ax_rng_to_trg_det.plot(t,dist_to_target,linestyle=":",marker=".",markersize=0.5)
        legend.append(all_general_info["ordering"][n])

    lr = [0, t[-1]]

    ax_rng_to_trg_det.plot(lr,agent_info[n]["slower_rng"]*np.ones([2,1]),linestyle="--",c="m",linewidth=3)
    ax_rng_to_trg_det.plot(lr,agent_info[n]["ideal_rng"]*np.ones([2,1]),linestyle=":",c="g",linewidth=1)
    ax_rng_to_trg_det.plot(lr,agent_info[n]["faster_rng"]*np.ones([2,1]),linestyle="--",c="m",linewidth=3)

    #legend.extend(["Slow Down Range", "Ideal Range", "Faster Range"])
    ax_rng_to_trg_det.legend(legend,
                            ncol=1,
                            fontsize=6,
                            borderpad=0,
                            labelspacing=0,
                            loc = 'center left',
                            bbox_to_anchor=(1,0.5))
    
    ax_rng_to_trg_det.set_ylim([agent_info[n]["slower_rng"]-agent_info[n]["slower_rng"]*0.5, agent_info[n]["faster_rng"]+agent_info[n]["faster_rng"]*0.5])

    ax_rng_to_trg_det.set_title("Distance to target",fontsize=6)
    ax_rng_to_trg_det.set_yticklabels(ax_rng_to_trg_det.get_yticklabels(),fontsize=6)
    ax_rng_to_trg_det.grid(True)


    ax_heading_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_spd_chngs_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_rng_to_trg_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    

    #Now we plot the near misses and collisions w/rt to time
    nm = all_data_df["near_miss_total"]
    cl = all_data_df["collision_total"]

    ax_nm_and_cols_det.plot(t,nm)
    ax_nm_and_cols_det.plot(t,cl)
    ax_nm_and_cols_det.legend(["Near Misses", "Collisions"],
                                ncol=1,
                                fontsize=6,
                                borderpad=0,
                                labelspacing=0)
    pos = ax_nm_and_cols_det.get_position()
    ax_nm_and_cols_det.set_position([0.125,0.45,0.352,0.15])
    ax_nm_and_cols_det.grid(True)

    #The Y axis is the order of the agents, the collective convoy is idx 0
    legend_markers = []
    max_order = 0
    for k,v in agent_info.items():
        if k == all_general_info['leader']:
            continue
        order = all_general_info['ordering'][k]
        if order > max_order:
            max_order = order
        ax_in_convoy_det.scatter(t,all_data_df[f"{k}_in_rng"]*order,s=1.5)
        legend_markers.append(f"{order}")
    legend_markers.append(f"All")
    ax_in_convoy_det.scatter(t,all_data_df["all_in_range"],s=1.5)
    ax_in_convoy_det.set_ylim([0.2,max_order+1])
    ax_in_convoy_det.grid(True)
    ax_in_convoy_det.set_title("In convoy (bool)",fontsize=6)
    ax_in_convoy_det.set_yticklabels(ax_in_convoy_det.get_yticklabels(),fontsize=6)
    ax_in_convoy_det.set_ylabel("Agent order",fontsize=6)
    ax_in_convoy_det.set_xlabel("Time (s)",fontsize=6)

    ax_in_convoy_det.legend(legend_markers,
                            ncol=1,
                            fontsize=6,
                            borderpad=0,
                            labelspacing=0,
                            loc = 'center left',
                            bbox_to_anchor=(1,0.5))

    #Now plot a histogram of the total time each agent spent within a histogram
    #Sort the order they are plotted by the order in which they are in
    # all_agents_sum, follower_1, follower_2, ...

    # Consider % time spent in convoy
    # Consider the average range from target
    try:
        times_entered_convoy = all_data_df["all_in_range_transition"].value_counts()[1]
    except:
        times_entered_convoy = 0
    
    try:
        times_exited_convoy = all_data_df["all_in_range_transition"].value_counts()[-1]
    except:
        times_exited_convoy = 0

    

    total_time_in_convoy = dict()
    mission_duration = all_data_df.index[-1]

    

    for a in agent_names:
        if a == all_general_info['leader']:
            continue
        #Take differences in time for all measurements, for all cases in which this agent is also in a convoy, take the cummulative time of the 
        a_in_convoy = all_data_df[f"{a}_in_rng"]
        iic = np.array(t_diff[a_in_convoy])
        iic = iic[~np.isnan(iic)] 
        total_time_in_convoy[a] = iic.sum()/mission_duration
    all_in_convoy = all_data_df[f"all_in_range"] 
    total_time_in_convoy['all'] = np.array(t_diff[all_in_convoy]).sum()/mission_duration
    

    x = ["all_agents"]
    y = [total_time_in_convoy['all']]

    ordering_sortable = [(k,v) for k,v in all_general_info['ordering'].items()]
    ordering = sorted(ordering_sortable,key=lambda k: k[1])
    rl = dict([(v,k) for k,v in all_general_info['ordering'].items()])
    
    x.extend([f"{k}_{v}" for k,v in ordering if k != ln])
    y.extend([total_time_in_convoy[rl[v]] for k,v in ordering if k != ln])

    
    # Plotting the % time in which an agent is in a convoy w/rt mission duration
    barplot = ax_perc_in_convoy_det.bar(x,y,color="darkorange")
    ax_perc_in_convoy_det.set_xticklabels(x,rotation=45,fontsize=8)
    
    ax_perc_in_convoy_det.set_ylabel("Prop. Time in Convoy",fontsize=8)
    ax_perc_in_convoy_det.set_yticks(np.linspace(-0.1,1.1,6).round())
    ax_perc_in_convoy_det.bar_label(barplot, [f"{p*100:0.0f}%" for p in y],fontsize=8)
    ax_perc_in_convoy_det.grid(False)
    ax_perc_in_convoy_det.set_position([0.125,0.26,0.352,0.15])
    

    # Plotting the desired rudder/desired thrust for each of the agents
    legend = []
    for n in agent_names:
        rudder = all_data_df[f"{n}_rudder"]
        ax_rudder_det.plot(t,rudder,linestyle=":",marker=".",markersize=0.5)
        legend.append(all_general_info["ordering"][n])

    ax_rudder_det.legend(legend,
                        ncol=1,
                        fontsize=6,
                        borderpad=0,
                        labelspacing=0,
                        loc = 'center left',
                        bbox_to_anchor=(1,0.5))
    ax_rudder_det.set_ylim([-101, 101])

    ax_rudder_det.set_title("Rudder",fontsize=6)
    ax_rudder_det.set_yticklabels(ax_rudder_det.get_yticklabels(),fontsize=6)

    legend = []
    for n in agent_names:
        thrust = all_data_df[f"{n}_thrust"]
        ax_thrust_det.plot(t,thrust,linestyle=":",marker=".",markersize=0.5)
        legend.append(all_general_info["ordering"][n])

    ax_thrust_det.legend(legend,
                        ncol=1,
                        fontsize=6,
                        borderpad=0,
                        labelspacing=0,
                        loc = 'center left',
                        bbox_to_anchor=(1,0.5))
    
    ax_thrust_det.set_ylim([-1, 101])

    ax_thrust_det.set_title("Thrust",fontsize=6)

    ax_thrust_det.set_yticklabels(ax_thrust_det.get_yticklabels(),fontsize=6)

    ax_thrust_det.grid(True)
    """
    ax_thrust_det.get_shared_x_axes().join(ax_thrust_det, 
                                           ax_rudder_det, 
                                           ax_in_convoy_det,
                                           ax_rng_to_trg_det,
                                           ax_spd_chngs_det,
                                           ax_heading_det)
    """


    ax_heading_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_spd_chngs_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_rng_to_trg_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    #ax6_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_rudder_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )
    ax_thrust_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )

    #ax8_det.tick_params(labelleft=True, labelbottom=False, left=False, right=False )

    fig_det.suptitle(f"Detailed Synopsis {mission_hash} ")



    plt.savefig(f"{output_directory}{mission_hash}_det.png", dpi=100)
    plt.close()
    ###### <Detailed analysis driven plot>



    ###### </PLOT ALL THE DATA>

    ###### <DUMP HIGH LEVEL DATA QUANTIFYING A MISSION>


    p_idx = mission_directory.find("P")
    k_idx = mission_directory.find("K")

    configuration_idx = mission_hash[1:p_idx]
    param_idx = mission_hash[p_idx+1:k_idx]
    trial = mission_hash[k_idx+1:]

    #TODO: Output all the metrics we care about to a file
    # ALL: trial, configuration idx, parameter idx, n agents, straightness index, turn index, near misses, collisions, % time in convoy
    # N AGENT: name, order, straightness index, turn index, average distance from target, % time in convoy
    # TODO: Consider variances in control effort
    # TODO: Consider a time in optimal state (more exclusive conditions which defines 'optimal')
    # TODO: Consider convoy cohesion - how similar are all the agents speeds at any given time
    # TODO: Consider an agents variation in control effort (DESIRED_THRUST, DESIRED_RUDDER)
    with open(f"{output_directory}{mission_hash}.txt", "w") as f:
        #For all agents
        ##Trial number, configuration index, parameter index, number of agents, straightness index, turn index, near misses, collisions, fractional time in convoy, times entered convoy, times exited convoy
    
        f.write(f"ALL:t={trial},c={configuration_idx},p={param_idx},na={len(agent_names)},si={straightness_index},ti={turn_index},nm={near_misses},co={collisions},ptic={total_time_in_convoy['all']},tenc={times_entered_convoy},texc={times_exited_convoy}\n")
        f.write(f"VARIABLES:")
        for idx, (k, v) in enumerate(agent_variables.items()):
            f.write(f"{k}={v}")
            if idx == len(agent_variables)-1:
                f.write("\n")
            else:
                f.write(",")
        #In the convoy order, print specific agent information, including percent time in convoy (as 0-1), speed standard deviation, straightness index, turning index, and mean deviation from ideal range
        for idx in range(1,len(agent_names)+1):
            an = rl[idx]
            percent_time_in_convoy = total_time_in_convoy[f"{an}"] if an != all_general_info["leader"] else -1
            speed_std = all_data_df[f"{an}_spd"].std()
            agent_straightness = agent_straightnesses[an]
            agent_turniness = agent_turninesses[an]
            agent_dev_from_ideal_rng = all_data_df[f"{an}_rng_dev"].mean() if an != all_general_info["leader"] else -1
            line = f"{idx},{percent_time_in_convoy:0.2f},{speed_std:0.1f},{agent_straightness:0.3f},{agent_turniness:0.3f},{agent_dev_from_ideal_rng:0.2f}"
            f.write(f"{line}")
            if idx != len(agent_name)+2:
                f.write("\n")
    ###### </DUMP HIGH LEVEL DATA QUANTIFYING A MISSION>

    ###### <END>
