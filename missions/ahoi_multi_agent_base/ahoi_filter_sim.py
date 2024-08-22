import numpy as np
import pandas as pd
import time
from datetime import datetime as d_time, timedelta as t_delta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import ahoi_ekf_base
from ahoi_filter_utilities import *

    
rwdl = RealWorldDataLoader(ahoi_csv='2024-08-05_01_mobile_node/ahoi_interface_log_20240805_190152.csv',
                           mobile_csv='2024-08-05_01_mdm/LOG_OAK_5_8_2024_____18_34_20/log_oak_5_8_2024_____18_34_20_alog_csvs/NODE_REPORT_LOCAL.csv', 
                           id2_csv='2024-08-05_01_mdm/LOG_NED_5_8_2024_____18_34_13/log_ned_5_8_2024_____18_34_13_alog_csvs/NODE_REPORT_LOCAL.csv',
                           id6_csv='2024-08-05_01_mdm/LOG_ABE_5_8_2024_____18_34_05/log_abe_5_8_2024_____18_34_05_alog_csvs/NODE_REPORT_LOCAL.csv', 
                           id9_csv='2024-08-05_01_mdm/LOG_MAX_5_8_2024_____18_33_54/log_max_5_8_2024_____18_33_54_alog_csvs/NODE_REPORT_LOCAL.csv', 
                           rel_path = 'missions/ahoi_multi_agent_base/logs/',
                           anchor_labels = {2: 'NED - 2', 6: 'ABE - 6', 9: 'MAX - 9',99: 'NA'})

rwdl.set_start_end(start_utc=d_time(2024, 8, 5, 23, 3, 0), 
                   end_utc=d_time(2024, 8, 5, 23, 4, 30))

rwdl.get_anchor_dfs() # anchor df - output: id2, id6, id9
rwdl.get_mobile_df()


# =============================================================================
# =============================================================================
# =============================================================================

# Initializing EKF parameters

auv_dim_state = 3
ahoi_dim_meas = 1
#EKF state: [x, y, z, roll, pitch, yaw, dx, dy, dz] #droll, dpitch, dyaw]
x0_est = np.array([20, -30, 1])

p_mat_est = np.diag([15, 15, 0.0])

dt_sec = 0.05
process_noise_mat = np.diag([2, 2, 0.0])#*dt_sec
meas_noise_ahoi = 50
meas_noise_yaw = 1
# Create an instance of the EKF
ahoi_ekf = ahoi_ekf_base.EKF_Node(auv_dim_state, ahoi_dim_meas,
                                  process_model_type="simple",process_noise=process_noise_mat,
                                  x0_est=x0_est, p_mat_est=p_mat_est)



mobile_node_df = rwdl.get_mobile_df()
ahoi_df = rwdl.get_ahoi_df()
anchor_dist_df = rwdl.get_all_anchor_dist_df()
anchor_all_data_df = rwdl.get_all_anchor_data_df()

# Dictionary to store all dynamic anchor positions over sequences by anchor ID
anchor_estimator = AnchorEstimator([2,6,9])
#

# =============================================================================

# Iterate over each sequence number
#sequence_numbers = ahoi_df['sequence_number'].unique()


scale_for_SoS = 1500/1500

start_time_utc, end_time_utc = rwdl.get_start_end_utc()
#start_time_utc = datetime(2024, 8, 5, 23, 4, 15) 
#end_time_utc = datetime(2024, 8, 5, 23, 2, 45)
#rwdl.set_start_end(start_utc=start_time_utc, end_utc=end_time_utc)


dt = t_delta(seconds=dt_sec) # TODO: can currently only handle one update / data row per time step

current_time = start_time_utc
data_index = 1
ahoi_data_df_mgt = DFReader(ahoi_df, start_idx=data_index)

gt_data_index = 4
anchor_dist_df_mgt = DFReader(anchor_dist_df, start_idx=gt_data_index)

anchor_all_data_df_mgt = DFReader(anchor_all_data_df, start_idx=gt_data_index)

new_poll = False
new_meas = False


#use_data = 'ahoi' #
use_data = 'ground_truth_dist'
event_type = ''


# List to store estimated positions
x_est_list = []
time_steps_list = []
y_delta_dist_list = []
y_update_time_list = []

debug_plotting = True
if debug_plotting:
    plt.ion()

poll_time = current_time
event_time = current_time
last_meas_time = current_time   
ahoi_meas = AhoiMeasurement() # from utilities


poll_tof_open = False
poll_pos_open = False
sequence_id = 0
anchor_order_idx = 0

new_meas_update = False

anchor_order_dict = {0:2, 1:6, 2:9}
polling_scheme_dict = {0:'TOF-POS-poll', 1:'TOF-poll',2:'TOF-poll'}

polling_type_idx = np.zeros((len(anchor_order_dict),), dtype=int) # current polling type for each anchor

# =============================================================================
# ========================== EKF - LOOP =======================================
# =============================================================================
fig, ax = plt.subplots(1, 1)
while current_time < anchor_dist_df_mgt.get_end_time(): 
    current_time += dt
    # Predict the next state
    ahoi_ekf.predict(dt_sim=dt)

    # Store the predicted position
    x_est_list.append(ahoi_ekf.get_x_est().copy())

    time_steps_list.append(current_time)

    if anchor_dist_df_mgt.check_end_of_data():
        break
    current_gt_distances = anchor_dist_df_mgt.get_recent_data_at(current_time)
    current_anchor_data = anchor_all_data_df_mgt.get_recent_data_at(current_time)


    #return event_type, event_time, sequence_id, polled_anchor_id, new_data_row

    # =============================================================================
    #     # sim measurements
    # =============================================================================


    time_reply_tof_poll = 0.65 # t_delta(seconds=0.65)
    time_reply_pos_poll = 1.25 # t_delta(seconds=1.25)
    time_out_tof = 0.7 # t_delta(seconds=0.7)
    time_out_pos = 1.3 # t_delta(seconds=1.3)

    time_since_poll = (current_time-poll_time).total_seconds()

    # =============================================================================
    #     # sim measurements
    # =============================================================================
    replay_base = 'real'#'sim-from-gps'
    if replay_base == 'sim-from-gps':
        
        # -------------------------------------------
        # trigger new poll
        # -------------------------------------------
        if not poll_tof_open and not poll_pos_open:
            # no open? issue new poll according to polling scheme

            # get next anchor to poll
            polled_anchor_id = anchor_order_dict[anchor_order_idx]

            # get polling idx -> type for selected anchor
            poll_type_idx = polling_type_idx[anchor_order_idx]
            #print(f"\n id{polled_anchor_id} to select:{poll_type_idx} from {polling_type_idx}")
            event_type = polling_scheme_dict[poll_type_idx]
            event_time = current_time
            poll_time = current_time

            if event_type == 'TOF-poll':
                poll_tof_open = True
                poll_pos_open = False
            elif event_type == 'TOF-POS-poll':
                poll_tof_open = True
                poll_pos_open = True
            else:
                print("Error: Poll type not found")

            new_poll = True
            time_since_poll = (current_time-poll_time).total_seconds()
            sequence_id = (sequence_id + 1) % 256
            #print(f"sequence_id {sequence_id} polling {event_type} for anchor {polled_anchor_id}")

            
            # optional: write poll to df or csv [poll_time, event_type, target_anchor_id]

            
            # update polling type for current anchor
            polling_type_idx[anchor_order_idx] += 1
            if polling_type_idx[anchor_order_idx] == len(polling_scheme_dict):  
                polling_type_idx[anchor_order_idx] = 0

            # go to next anchor
            anchor_order_idx += 1
            if anchor_order_idx == len(anchor_order_dict):
                anchor_order_idx = 0


            #print(f"After poll anchor_order_idx {anchor_order_idx} polling_type_idx {polling_type_idx}")

            

            #if anchor_order_idx == 0:
                # all anchors polled, increment polling type

                # for current anchor, update polling type
                # this can also be done after successful reply -> retry otherwise
                


        # -------------------------------------------
        # ACK on TOF-poll - if open and min time passed
        # -------------------------------------------
        if poll_tof_open and time_since_poll >= time_reply_tof_poll:
            # received TOF-poll (can be part of TOF-POS-poll)
            # reply with TOF-ACK

            # TODO: add random failure --> pass

            poll_tof_open = False
            
            event_type = 'TOF-ACK'
            event_time = current_time
            # TODO: MEASUREMENT: get range from anchor
            if  polled_anchor_id == 2:
                received_range = current_anchor_data['id2_dist']
                
            elif polled_anchor_id == 6:
                received_range = current_anchor_data['id6_dist']
                
            elif polled_anchor_id == 9:
                received_range = current_anchor_data['id9_dist']
              
            new_meas = True
            

        if poll_pos_open and time_since_poll >= time_reply_pos_poll:
            # received POS-poll (is part of TOF-POS-poll)
            # reply with POS-ACK

            # TODO: add random failure --> pass

            poll_pos_open = False
           
            event_type = 'POS-ACK'
            event_time = current_time
            # TODO: MEASUREMENT: get pos from anchor
            
            if  polled_anchor_id == 2:
                received_pos = current_anchor_data[['id2_X', 'id2_Y']].values.ravel()
            elif polled_anchor_id == 6:
                received_pos = current_anchor_data[['id6_X', 'id6_Y']].values.ravel()
            elif polled_anchor_id == 9:
                received_pos = current_anchor_data[['id9_X', 'id9_Y']].values.ravel()
            else:
                print("Error: Anchor ID not found")

            new_meas = True

        if poll_tof_open and time_since_poll > time_out_tof:
            poll_tof_open = False
            print(f"TOF poll timed out for anchor {polled_anchor_id} at {current_time}")

        if poll_pos_open and time_since_poll > time_out_pos:
            poll_pos_open = False
            print(f"POS poll timed out for anchor {polled_anchor_id} at {current_time}")

    # =============================================================================
    #   process measurement data
    # 
    #   new_poll / new_meas
    #    
    #   event_time - datetime
    #   event_type
    #   sequence_id
    #   polled_anchor_id
    #   received_range
    #   received_pos
    #
    # =============================================================================




    # =============================================================================
    #   get new data ahoi-df, ground truth distances 
    # =============================================================================
    elif replay_base == 'real':

        if ahoi_data_df_mgt.to_next_data_row(current_time): # true if this returns a new data row
            #print("hello")
            new_data_row = ahoi_data_df_mgt.get_newest_data()
            if new_data_row['event'] == 'range_poll':
                event_type = 'TOF-POS-poll'
            else:
                event_type = new_data_row['event']

            event_time = new_data_row['time']
            sequence_id = new_data_row['sequence_number']
            #print(f"event type: {event_type}, time: {event_time}, seq: {sequence_id}")

            if event_type == 'TOF-POS-poll':
                polled_anchor_id =  new_data_row['target_id']
            else:
                polled_anchor_id = new_data_row['anchor_id']
            new_poll = True
        

        if new_poll and event_type == 'TOF-ACK':

            if use_data == 'ahoi':
                received_range = new_data_row['distance']
            
            elif use_data == 'ground_truth_dist':
                polled_anchor_id= new_data_row['anchor_id']
                if  polled_anchor_id == 2:
                    received_range = current_gt_distances['id2_dist']
                elif polled_anchor_id == 6:
                    received_range = current_gt_distances['id6_dist']
                elif polled_anchor_id == 9:
                    received_range = current_gt_distances['id9_dist']
                
            new_meas = True
            new_poll = False

        elif new_poll and event_type == 'POS-ACK':
            if use_data == 'ahoi' or use_data == 'ground_truth_dist':
                polled_anchor_id = new_data_row['anchor_id']
                received_pos = new_data_row[['pos_x','pos_y']].values.ravel()

            new_meas = True
            new_poll = False

    # =============================================================================
    #   process measurement data
    # 
    #   new_poll / new_meas
    #    
    #   event_time
    #   event_type
    #   sequence_id
    #   polled_anchor_id
    #   received_range
    #   received_pos
    #
    # =============================================================================

    if new_poll and (event_type =='TOF-POS-poll' or event_type =='TOF-poll'):
        ahoi_meas.reset(reset_type='full')
        ahoi_meas.issued_poll(poll_type=event_type,
                              poll_time=event_time,
                              seq_id=sequence_id, 
                              anchor_id=polled_anchor_id)
        #print(f"polling anchor {polled_anchor_id} w {event_type}")
        event_type = ''
        new_poll = False

        
    elif new_meas and event_type =='TOF-ACK':

        ahoi_meas.received_range(rec_range=received_range, 
                                 rec_range_time=event_time, 
                                 seq_i=sequence_id)
        event_type = ''
        new_meas = False
        
    elif new_meas and event_type =='POS-ACK':       
        x, y = received_pos
        anchor_id = polled_anchor_id

        ahoi_meas.received_pos(rec_pos=np.array([x,y,0]), 
                                rec_pos_time=event_time, 
                                seq_i=sequence_id)

        event_type = ''
        new_meas = False


    

    # =============================================================================
    # Update Anchors Estimator
    # =============================================================================
    if ahoi_meas.got_pos():
        anchor_pos3d, meas_anchor_id, time_pos = ahoi_meas.get_anchor_pos()
        # TODO: velocity currently needs to be updated before position
        vel = anchor_estimator.get_anchor(meas_anchor_id).comp_vel(pos=anchor_pos3d, time_pos=time_pos)
        anchor_estimator.get_anchor(meas_anchor_id).update_pos(pos3d=anchor_pos3d, timestamp=time_pos) # this time is much newer/more recent than the position time
        
        print(f"ID:{meas_anchor_id} updated -> Anchor velocity {np.linalg.norm(vel):.2f}m/s")

        
        


    # =============================================================================
    #   Update EKF with TOF measurements
    # =============================================================================
    if ahoi_meas.got_range(): 
        meas_range, meas_anchor_id, time_range = ahoi_meas.get_range()
        if anchor_estimator.get_anchor(meas_anchor_id).is_init():
 
            anchor_pos3d,_ = anchor_estimator.get_anchor(meas_anchor_id).get_last_pos()    

            y_delta_dist, z_meas, z_est_anchor = ahoi_ekf.dist_measurement_update(dist_meas=meas_range, 
                                                                                anchor_pos=anchor_pos3d, 
                                                                                w_mat_dist=meas_noise_ahoi)
            ahoi_meas.reset(reset_type='TOF') # Measurement has been used - reset poll
            #print(f"Anchor {meas_anchor_id} EKF-Range update")
            
            new_meas_update = True

    if new_meas_update:
        y_delta_dist_list.append((meas_anchor_id, anchor_pos3d, y_delta_dist, z_meas, z_est_anchor))
        y_update_time_list.append((current_time))

        
        #print(f"id:{meas_anchor_id} - meas {meas_range:.2f}m, z_meas {z_meas:.2f}m, z_est: {z_est_anchor:.2f}, y_delta {y_delta_dist:.2f}")
        print(f"ID:{meas_anchor_id} EKF-Range Update {(current_time-last_meas_time).total_seconds()}s since last update")
        last_meas_time = current_time
 
        
        time_steps_array = np.array(time_steps_list)
        new_meas_update = False


        if debug_plotting:  
            anchor_start= np.array([[ 44.69, -38.08],
                                    [ 19.43, -21.32],
                                    [ 28.73, -64.63]])
            
            x_est_list.append(ahoi_ekf.get_x_est().copy())
            x_est_array = np.array(x_est_list)



            ax.clear() # Clear the previous plot
            mobile_cropped = rwdl.df_clip_time(mobile_node_df, start_time_utc, current_time)
            ax.plot(mobile_cropped['X'], mobile_cropped['Y'], color='purple', linestyle='-', marker='*', label='mobile node')
            ax.plot(x_est_array[:,0], x_est_array[:,1], marker='o')
            ax.plot(x_est_array[-2:,0], x_est_array[-2:,1], marker='o', color='magenta')
            
            ax.scatter(anchor_pos3d[0], anchor_pos3d[1], color='r')
            ax.scatter(anchor_start[:,0], anchor_start[:,1], marker='*')
            c_meas = plt.Circle((anchor_pos3d[0], anchor_pos3d[1]), z_meas, color='r', fill=False, label='z_meas')
            c_est = plt.Circle((anchor_pos3d[0], anchor_pos3d[1]), z_est_anchor, color='b', fill=False, label='z_est')
            
            ax.add_patch(c_meas)
            ax.add_patch(c_est)
            
            ax.legend()
            ax.set_aspect('equal', 'box')
            ax.set_xlim((0,80))
            ax.set_ylim((-80,-0))
            ax.grid(True)
            
            plt.show()
            plt.pause(0.1)
            


    






    


# # Convert the list of estimated positions to a NumPy array
# x_est_array = np.array(x_est_list)
# time_steps_array = np.array(time_steps_list)
# #y_delta_dist_array = np.array(y_delta_dist_list)
# #y_update_time_array = np.array(y_update_time_list)


# print(f"len x : {x_est_array.shape}, len time steps {time_steps_array.shape}") #, len y_dist  {y_delta_dist_array.shape}, en y_dist_time  {y_update_time_array.shape}")

# # Create the plot layout using gridspec for custom layout
# fig = plt.figure(figsize=(12, 6))
# gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])

# # Plot the anchor positions in the left subplot
# ax0 = plt.subplot(gs[0])

# # Plot the estimated path
# ax0.plot(x_est_array[:, 0], x_est_array[:, 1], label='Oak est.', marker='o', linestyle='-')

# # Annotate the estimated path with sequence numbers for every 5th sequence
# n_label = 5
# #for idx, (x, y) in enumerate(zip(x_est_array[:, 0], x_est_array[:, 1])):
#     #if sequence_numbers[idx] % n_label == 0:
#     #    ax0.annotate(str(sequence_numbers[idx]), (x, y), textcoords="offset points", xytext=(0, 5), ha='center')
# ax0.annotate('X0_est', (x0_est[0], x0_est[1]), textcoords="offset points", xytext=(0, 5), ha='center')

# if use_moos_logs:
#     oak_clipped = df_mdm_mobile[(df_mdm_mobile['time'] >= start_time_utc) & (df_mdm_mobile['time'] <= end_time_utc)]
#     ax0.plot(oak_clipped['X'], oak_clipped['Y'], color='purple', linestyle='--', label='Oak')


# # Plot the anchor positions in x, y
# for anchor_id in pos_ack_data['anchor_id'].unique():
#     anchor_pos = pos_ack_data[pos_ack_data['anchor_id'] == anchor_id]
#     ax0.scatter(anchor_pos['pos_x'], anchor_pos['pos_y'], label=f'{anchor_labels[anchor_id]}', s=50, color=anchor_colors[anchor_id])

# ax0.set_xlabel('Position X')
# ax0.set_ylabel('Position Y')
# ax0.set_title('Anchor and Individual Positions')
# ax0.legend()
# ax0.axis('equal')
# ax0.grid(True)

# # Create subplots for Abe's X and Y over time stacked on the right
# gs_right = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs[1], hspace=0.4)


# anchor_df = pos_ack_data[pos_ack_data['anchor_id'] == 6][['time', 'pos_x', 'pos_y']]


# ax1 = plt.subplot(gs_right[0])
# if use_moos_logs:
#     ax1.plot(oak_clipped['time'], oak_clipped['X'], linestyle='--',  color='purple', label='Oak X')
# ax1.plot(time_steps_array, x_est_array[:,0], marker='^',label='Received via ahoi')
# ax1.set_xlabel('Time')
# ax1.set_ylabel('X Position')
# ax1.set_title("X Position Over Time")
# ax1.legend()
# ax1.grid(True)

# # Plot Abe's Y position over time in the second subplot on the right
# ax2 = plt.subplot(gs_right[1])
# if use_moos_logs:
#     ax2.plot(oak_clipped['time'], oak_clipped['Y'], linestyle='--',  color='purple', label='Oak Y')
# ax2.plot(time_steps_array, x_est_array[:,1], marker='^',label='Received via ahoi')
# ax2.set_xlabel('Time')
# ax2.set_ylabel('Y Position')
# ax2.set_title("Y Position Over Time")
# ax2.legend()
# ax2.grid(True)

# ax3 = plt.subplot(gs_right[2])

# for anchor_id in tof_ack_data['anchor_id'].unique():
#     anchor_data = tof_ack_data[tof_ack_data['anchor_id'] == anchor_id]
#     ax3.scatter(anchor_data['time'], anchor_data['distance']*scale_for_SoS, label=f'{anchor_labels[anchor_id]}', marker='o', color=anchor_colors[anchor_id])

# if use_moos_logs:
#     # NED - 2, ABE - 6, MAX - 9
#     # anchor_colors = {2: 'b', 6: 'g', 9: 'orange'}
#     ax3.plot(distances_combined['time'], distances_combined['Distance_Abe'], color=anchor_colors[6])
#     ax3.plot(distances_combined['time'], distances_combined['Distance_Max'], color=anchor_colors[9])
#     ax3.plot(distances_combined['time'], distances_combined['Distance_Ned'], color=anchor_colors[2])

# ax3.set_ylabel('Distance in m')

# #ax3.set_title('Distances by Anchor Over Sequence Numbers')
# ax3.legend()
# ax3.grid(True)


# plt.tight_layout()
# plt.show()