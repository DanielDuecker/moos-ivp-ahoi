#!/bin/python3

###### <START>

if __name__ == "__main__":
    import sys
    import os
    import json 
    import glob
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.pyplot
    from scipy.spatial.transform import Rotation as R

    
    import numpy as np
    import pandas as pd
    from matplotlib.path import Path
    import warnings
    warnings.filterwarnings("ignore") #matplotlib and pandas are too verbose

    ###### <SETUP>
    mission_directory = sys.argv[1]
    mission_hash = mission_directory.split("/")[-1]
    glb = glob.glob(f"{mission_directory}/*_tmp/*whole.json")
    fname = glb[0]
    output_directory = f"{mission_directory}_meta/"
    try:
        os.mkdir(output_directory)
    except OSError:
        pass 
    
    ##### Open all the configuration and data files we need to obtain preceding information
    #Load the JSON file
    mission_data = json.load(open(fname))

    ###### </SETUP>
    mission = next(iter(mission_data))

    to_plot = {'DESIRED_RUDDER':"f",
               'DESIRED_PORT_ELEVATOR':"f", 
               'DESIRED_STBD_ELEVATOR':"f", 
               'DESIRED_THRUST':"f", 
               'DESIRED_HEADING':"f", 
               'DESIRED_PITCH':"f", 
               'DESIRED_SPEED':"f", 
               'NAV_DEPTH':"f", 
               'DESIRED_DEPTH':"f", 
               'PROJECTED_NAV_DEPTH':"f", 
               "NAV_ROLL":"f",
               "NAV_PITCH":"f", 
               "NAV_YAW":"f", 
               "NAV_HEADING":"f",
               "RPI_TEMP":"f", 
               "MISSION_COMPLETE":"s", 
               "IN_WATER":"s", 
               "NVGR_CURRENT":"f",
               "NVGR_VOLTAGE":"f",
               "NVGR_ROLLING_CURRENT":"f",
               "NVGR_ROLLING_VOLTAGE":"f",
               "NVGR_ROLLING_POWER":"f",
               "NVGTR_IT_C":"f",
               "ADAPT_CONSTS":"s",
               "SLIDING_ROLL":"f",
               "SLIDING_PITCH":"f",
               "SLIDING_YAW":"f",
               "EFFORT_ROLL":"f",
               "EFFORT_PITCH":"f",
               "EFFORT_YAW":"f",
               "SMOOTH_DESIRED_HEADING":"f",
               "SMOOTH_DESIRED_PITCH":"f",
               "SMOOTH_DESIRED_ROLL":"f",
               "SMOOTH_DESIRED_DEPTH":"f",
               "SMOOTH_DESIRED_HEADING_DOT":"f",
               "SMOOTH_DESIRED_PITCH_DOT":"f",
               "SMOOTH_DESIRED_ROLL_DOT":"f",
               "NAV_ROLL_DOT":"f",
               "NAV_PITCH_DOT":"f",
               "NAV_HEADING_DOT":"f",
               "NAV_LAT":"f",
               "NAV_LON":"f",
               "NAV_X_GPS":"f",
               "NAV_Y_GPS":"f",
               "PDC_ROLL":"f",
               "PDC_PITCH":"f",
               "PDC_YAW":"f",
               "ADC_ROLL":"f",
               "ADC_PITCH":"f",
               "ADC_YAW":"f",
               "GPS_X":"f",
               "GPS_Y":"f",
               "ADC_YAW":"f"
               }
    
    t_idx = 0
    d_idx = 1

    all_data = []

    n_params = 0

    info = mission_data[mission]['info']
    alias = info["alias"]
    log_start = info["logstart"]
    open_date = info["opendate"]
    lf = info["logfile"]

    #print(mission_data[mission]['data'].keys())

    def cast(dat,var):
        var = var.lower()
        if(var == "f"):
            return float(dat)
        elif(var == "i"):
            return int(dat)
        elif(var == "s"):
            return str(dat)
        
    #for everything we want to plot
    raw_data = mission_data[mission]['data']

    # for elem in raw_data.keys():
    #     print(elem)

    for k,v in to_plot.items():
        #go through each datapoint, knowing that the times are not synchronized yet - form individual dataframes and pack them in list
        if k in raw_data:
            set = [[entry[0]-log_start,cast((entry[1]), v)] for entry in raw_data[k]]
            if k == "ADAPT_CONSTS":
                for idx, elem in enumerate(set):
                    entry = [elem[0]]
                    entry.extend([cast(a,"f") for a in elem[1].split("|")])
                    set[idx] = entry
                cnames = ["time"]
                cnames.extend([f'adapt_const_{i}' for i in range(1,len(entry))])
                df = pd.DataFrame(set,columns=cnames).set_index("time")
                n_params = len(entry)-1
                print("--Runtime adaptive constants--")
                print(df.describe())
                print("<--Runtime adaptive constants-->")
            else:
                df = pd.DataFrame(set,columns=["time", k.lower()]).set_index("time")
            all_data.append(df)
    
    data_df = all_data.pop()

    for elem in all_data:
        data_df = data_df.join(elem,how='outer')

    data_df["desired_roll"] = 0

    #We assume ZOH, in the sense that a message to the MOOSDB is the start of a new state fill forward
        
    # Include 10 seconds before in_water = true
    data_df["in_water"].fillna("false", inplace=True)
    data_df['in_water'] = data_df['in_water'].map({'true': True, 'false': False})

    # Include 10 seconds after mission_complete = true
    data_df["mission_complete"].fillna("false", inplace=True)
    data_df['mission_complete'] = data_df['mission_complete'].map({'true': True, 'false': False})
    
    data_df.fillna(method='ffill',inplace=True)

    #All NaNs that remain, is in the very start of the mission when agents are being brought online, such that 
    # no data exists to be filled forward (drop it)
    data_df.dropna(inplace=True)
    
    data_df["t"] = data_df.index.to_numpy() #create a column of equivalent indices

    mission_start_index = data_df['in_water'].idxmax()
    t_start = data_df.loc[mission_start_index]['t']

    if isinstance(t_start, pd.Series):
        t_start = t_start.iloc[0]

    mission_complete_index = data_df['mission_complete'].idxmax()
    t_end = data_df.loc[mission_complete_index]['t']

    if isinstance(t_end, pd.Series):
        t_end = t_end.iloc[0]
    
    # Calculate the timestamp 10 seconds after mission_complete
    t_window_pre = 20
    t_window_post = 20
    
    slc = (data_df['t'] <= ( t_end + t_window_post)) & (data_df['t'] >= (t_start - t_window_pre))
    data_df_sliced = data_df[slc]

    """
        1) Plot the state estimates and the control efforts
    """

    rs = 9
    cs = 2
    fig = plt.figure(figsize=(12, 12))

    # Heading - [0-1]
    ax = plt.subplot2grid(shape=(rs,cs),loc=(0,0),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_heading'], color='black', linestyle='-', label='Desired Heading')
    #ax.plot(data_df_sliced.index, data_df_sliced['smooth_desired_heading'], color='black', linestyle='--')
    ax.plot(data_df_sliced.index, data_df_sliced['nav_heading'], color='blue', linestyle=':', label='Heading')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Angle (degrees)')
    ax.legend()
    ax.grid(True)

    # Pitch and depth [2-3]
    ax = plt.subplot2grid(shape=(rs,cs),loc=(2,0),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_pitch'], color='black', linestyle='-', label='Desired Pitch')
    #ax.plot(data_df_sliced.index, data_df_sliced['smooth_desired_pitch'], color='black', linestyle='--')
    ax.plot(data_df_sliced.index, data_df_sliced['nav_pitch'], color='green', linestyle=':', label='Pitch')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Angle (degrees)')
    ax.legend()
    ax.grid(True)

    # Roll - [4-5]
    ax = plt.subplot2grid(shape=(rs,cs),loc=(4,0),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_roll'], color='black', linestyle='-', label='Desired Roll')
    #ax.plot(data_df_sliced.index, data_df_sliced['smooth_desired_roll'], color='black', linestyle='--')
    ax.plot(data_df_sliced.index, data_df_sliced['nav_roll'], color='red', linestyle=':', label='Roll')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Angle (degrees)')
    ax.legend()
    ax.grid(True)

    # Depth [6-7]
    ax = plt.subplot2grid(shape=(rs,cs),loc=(6,0),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, -data_df_sliced['desired_depth'], color='black', linestyle='-', label='Desired Depth')
    #ax.plot(data_df_sliced.index, -data_df_sliced['smooth_desired_depth'], color='black', linestyle='--')
    ax.plot(data_df_sliced.index, -data_df_sliced['nav_depth'], color='blue', linestyle=':', label='Depth')
    # ax.plot(data_df_sliced.index, -data_df_sliced['projected_nav_depth'], color='red', linestyle='-', label='Projected Depth')
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Depth (meters)')
    ax.legend()
    ax.grid(True)

    # Elevator Efforts [8,9,10]
    ax = plt.subplot2grid(shape=(rs,cs),loc=(0,1),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_rudder'], color='red', linestyle='-', label='Rudder')
    ax.set_xlabel('Time')
    ax.set_ylabel('Fin Angle (%)')
    ax.set_ylim([-150,150])
    ax.legend()
    ax.grid(True)

    ax = plt.subplot2grid(shape=(rs,cs),loc=(2,1),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_stbd_elevator'], color='green', linestyle='-', label='Stbd_Elevator')
    ax.set_xlabel('Time')
    ax.set_ylabel('Fin Angle (%)')
    ax.set_ylim([-80,80])
    ax.legend()
    ax.grid(True)

    ax = plt.subplot2grid(shape=(rs,cs),loc=(4,1),rowspan=2,colspan=1)
    ax.plot(data_df_sliced.index, data_df_sliced['desired_port_elevator'], color='blue', linestyle='-', label='Port_Elevator')
    ax.set_ylim([-80,80])
    ax.set_xlabel('Time')
    ax.set_ylabel('Fin Angle (%)')
    ax.legend()
    ax.grid(True)

    # Plot voltage, current, and power on YY axis
    ax1 = plt.subplot2grid(shape=(rs,cs),loc=(6,1),rowspan=2,colspan=1)
    ax2 = ax1.twinx()
    ax1.plot(data_df_sliced.index, data_df_sliced['nvgr_voltage'], color='blue', label='Voltage')
    ax1.plot(data_df_sliced.index, data_df_sliced['nvgr_current'], color='red', label='Current')
    
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Voltage/Current', color='blue')
    ax1.set_ylim([0,18])
    ax2.plot(data_df_sliced.index, data_df_sliced['nvgr_rolling_power'], color='purple', label='Power')
    ax2.set_ylabel('Power (Watts)', color='purple')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax1.grid(True)

    plt.tight_layout()
    plt.savefig(output_directory + 'ss_ctrl_states.png', dpi=300, bbox_inches='tight')


    # Plot the estimated trajectory error
    """

        2) Consider a unit length in terms of time, and propagate the desired heading and the actual heading in terms of a unit X/Y

    """

    slc = (data_df['t'] <= ( t_end)) & (data_df['t'] >= (t_start))
    data_df_sliced_traj = data_df[slc]
    data_df_sliced_traj['t_mission'] = data_df_sliced_traj['t'] - data_df_sliced_traj['t'].iloc[0]
    data_df_sliced_traj['dt_mission'] = data_df_sliced_traj['t_mission'].diff().fillna(0)
    data_df_sliced_traj['des_h_rad'] = ((450 - data_df_sliced_traj['desired_heading'])%360)*np.pi/180
    data_df_sliced_traj['act_h_rad'] = ((450 - data_df_sliced_traj['nav_heading'])%360)*np.pi/180
    data_df_sliced_traj['t_mission'] = data_df_sliced_traj['t'] - data_df_sliced_traj['t'].iloc[0]
    data_df_sliced_traj['x_sim_des'] = data_df_sliced_traj['dt_mission']*np.cos(data_df_sliced_traj['des_h_rad'])
    data_df_sliced_traj['x_sim_des'] = data_df_sliced_traj['x_sim_des'].cumsum()
    data_df_sliced_traj['y_sim_des'] = data_df_sliced_traj['dt_mission']*np.sin(data_df_sliced_traj['des_h_rad'])
    data_df_sliced_traj['y_sim_des'] = data_df_sliced_traj['y_sim_des'].cumsum()

    data_df_sliced_traj['x_sim'] = data_df_sliced_traj['dt_mission']*np.cos(data_df_sliced_traj['act_h_rad'])
    data_df_sliced_traj['x_sim'] = data_df_sliced_traj['x_sim'].cumsum()
    data_df_sliced_traj['y_sim'] = data_df_sliced_traj['dt_mission']*np.sin(data_df_sliced_traj['act_h_rad'])
    data_df_sliced_traj['y_sim'] = data_df_sliced_traj['y_sim'].cumsum()

    rs = 4
    cs = 1
    fig = plt.figure(figsize=(6, 8))

    ax = plt.subplot2grid(shape=(rs,cs),loc=(0,0),rowspan=2,colspan=1)
    sc = ax.scatter(data_df_sliced_traj['x_sim_des'], data_df_sliced_traj['y_sim_des'],s=0.5,label='Desired',c='black')
    sc = ax.scatter(data_df_sliced_traj['x_sim'], data_df_sliced_traj['y_sim'], c=data_df_sliced_traj['t_mission'],s=0.5, label='Actual')
    cbar = plt.colorbar(sc,fraction=0.03)
    cbar.ax.tick_params(labelsize=6)
    ax.set_aspect('equal',adjustable='datalim')
    ax.set_xlabel("Easting (unit-length)",fontsize=10)
    ax.set_ylabel("Northing (unit-length)",fontsize=10)
    ax.grid(True)

    ax = plt.subplot2grid(shape=(rs,cs),loc=(2,0),rowspan=1,colspan=1)
    ax.plot(data_df_sliced_traj['t_mission'], data_df_sliced_traj['desired_heading'],color='black',label='Desired Heading')
    ax.plot(data_df_sliced_traj['t_mission'], data_df_sliced_traj['nav_heading'],color='red',label='Heading')
    ax.set_xlabel('Time')
    ax.set_ylabel('Heading')
    ax.legend()
    ax.grid(True)

    ax = plt.subplot2grid(shape=(rs,cs),loc=(3,0),rowspan=1,colspan=1)
    ax.plot(data_df_sliced_traj['t_mission'], -data_df_sliced_traj['desired_depth'],color='black',label='Desired Depth')
    #ax.plot(data_df_sliced['t_mission'], -data_df_sliced['smooth_desired_depth'],color='black', linestyle='--')
    ax.plot(data_df_sliced_traj['t_mission'], -data_df_sliced_traj['nav_depth'],color='green',label='Depth')
    # ax.plot(data_df_sliced['t_mission'], -data_df_sliced['projected_nav_depth'],color='red',label='Depth')
    ax.set_xlabel('Time')
    ax.set_ylabel('Depth')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(output_directory + 'est_traj.png', dpi=300, bbox_inches='tight')

    """ 
        3) We are now going to plot the fused IMU + Magnetometer on the Navigator board, and the HBK-CV7 AHRS
    """

    # Load matching CSV files for Navigator and HBK data
    nav_ahrs_file = glob.glob(f"{mission_directory}/*_Navigator_AHRS.csv")[0]  # Matching AHRS CSV file for Navigator
    dvl_pdx_file = glob.glob(f"{mission_directory}/*_Tracker650_PDX.csv")[0]  # 
    dvl_kfc_file = glob.glob(f"{mission_directory}/*_Tracker650_KFC.csv")[0]  # 
    filtered_accel_file = glob.glob(f"{mission_directory}/*_FilteredAccel.csv")[0]  # Matching filtered accel file for HBK
    filtered_gyro_file = glob.glob(f"{mission_directory}/*_FilteredGyro.csv")[0]  # Matching filtered gyro file for HBK
    filtered_mag_file = glob.glob(f"{mission_directory}/*_FilteredMag.csv")[0]  # Matching filtered mag file for HBK
    hbk_attitude_file = glob.glob(f"{mission_directory}/*_EulerAngles.csv")[0]  # Matching filtered mag file for HBK

    # Read the data from nav_ahrs_file
    nav_data = pd.read_csv(nav_ahrs_file)
    b = np.array([5.458541727396263, -6.006185354042229, 14.91588842409525])
    A = np.array([[1.0333825711846805, -0.006874626454690746, -0.004327871072470118],
                [-0.00687464135585194, 1.033517812548026, 0.003864412758002424],
                [-0.004327871072470118, 0.0038644124118864306, 1.0264179393243724]])
    nav_data[["Mag_1_X", "Mag_1_Y", "Mag_1_Z"]] = np.dot(nav_data[["Mag_1_X", "Mag_1_Y", "Mag_1_Z"]] - b, A.T)

    gyro_data = nav_data[['Gyro_X', 'Gyro_Y', 'Gyro_Z']].values
    accel_data = nav_data[['Imu_X', 'Imu_Y', 'Imu_Z']].values
    mag_data = nav_data[['Mag_1_X', 'Mag_1_Y', 'Mag_1_Z']].values
    timestamps = nav_data['TimeStamp'].values
    

    dvl_pdx_data = pd.read_csv(dvl_pdx_file)
    dvl_pdx_data.drop(columns=['angleDeltaRoll', 'angleDeltaPitch', 'angleDeltaYaw'], inplace=True)
    dvl_kfc_data = pd.read_csv(dvl_kfc_file)

    hbk_accel_data = pd.read_csv(filtered_accel_file)
    hbk_gyro_data = pd.read_csv(filtered_gyro_file)
    hbk_mag_data = pd.read_csv(filtered_mag_file)
    hbk_attitude_data = pd.read_csv(hbk_attitude_file)

    mag_mag = np.sqrt(nav_data['Mag_1_X']**2 + nav_data['Mag_1_Y']**2 + nav_data['Mag_1_Z']**2)

    # Normalize each column by the magnitude
    emfi = 51.3687
    #nav_data[['Mag_1_X', 'Mag_1_Y', 'Mag_1_Z']] = nav_data[['Mag_1_X', 'Mag_1_Y', 'Mag_1_Z']].div(mag_mag, axis=0)*emfi

    rotation_matrix_z = np.array([[-1, 0, 0],
                              [0, -1, 0],
                              [0, 0, 1]])
                              
    # Apply the rotation in place to Accelerometer data
    hbk_accel_data[['FilteredAccelX', 'FilteredAccelY', 'FilteredAccelZ']] = hbk_accel_data[['FilteredAccelX', 'FilteredAccelY', 'FilteredAccelZ']]

    # Apply the rotation in place to Gyroscope data
    hbk_gyro_data[['FilteredGyroX', 'FilteredGyroY', 'FilteredGyroZ']] = hbk_gyro_data[['FilteredGyroX', 'FilteredGyroY', 'FilteredGyroZ']].dot(rotation_matrix_z.T)

    # Apply the rotation in place to Magnetometer data
    hbk_mag_data[['FilteredMagX', 'FilteredMagY', 'FilteredMagZ']] = hbk_mag_data[['FilteredMagX', 'FilteredMagY', 'FilteredMagZ']].dot(rotation_matrix_z.T)

    hbk_attitude_data[["Roll", "Pitch", "Yaw"]] = hbk_attitude_data[["Roll", "Pitch", "Yaw"]]*180/np.pi
    hbk_attitude_data[["Roll", "Pitch", "Yaw"]] = hbk_attitude_data[["Roll", "Pitch", "Yaw"]].dot(rotation_matrix_z.T)
    # add a heading in degrees which is between 0 and 360
    hbk_attitude_data['Heading'] = (hbk_attitude_data['Yaw'] + 180 + -14.0833) % 360

    # Subtract log_start to get time relative to mission start
    nav_data['TimeStamp'] = nav_data['TimeStamp'] - log_start
    nav_data["t"] = nav_data['TimeStamp']
    nav_data.set_index('t', inplace=True)

    hbk_accel_data['Epoch'] = hbk_accel_data['Epoch'] - log_start
    hbk_gyro_data['Epoch'] = hbk_gyro_data['Epoch'] - log_start
    hbk_mag_data['Epoch'] = hbk_mag_data['Epoch'] - log_start
    hbk_attitude_data['Epoch'] = hbk_attitude_data['Epoch'] - log_start

    # Now apply the time slicing
    slc = (nav_data['TimeStamp'] <= (t_end + t_window_post)) & (nav_data['TimeStamp'] >= (t_start - t_window_pre))
    nav_data = nav_data[slc]

    slc = (hbk_accel_data['Epoch'] <= (t_end + t_window_post)) & (hbk_accel_data['Epoch'] >= (t_start - t_window_pre))
    hbk_accel_data = hbk_accel_data[slc]

    slc = (hbk_gyro_data['Epoch'] <= (t_end + t_window_post)) & (hbk_gyro_data['Epoch'] >= (t_start - t_window_pre))
    hbk_gyro_data = hbk_gyro_data[slc]

    slc = (hbk_mag_data['Epoch'] <= (t_end + t_window_post)) & (hbk_mag_data['Epoch'] >= (t_start - t_window_pre))
    hbk_mag_data = hbk_mag_data[slc]

    slc = (hbk_attitude_data['Epoch'] <= (t_end + t_window_post)) & (hbk_attitude_data['Epoch'] >= (t_start - t_window_pre))
    hbk_attitude_data = hbk_attitude_data[slc]

    # Extract relevant columns from CSV
    nav_time = data_df_sliced.index
    # nav_roll = nav_data['Roll']
    # nav_pitch = nav_data['Pitch']
    # nav_yaw = nav_data['Yaw']
    nav_roll = data_df_sliced['nav_roll']
    nav_pitch = data_df_sliced['nav_pitch']
    nav_heading = data_df_sliced['nav_heading']

    hbk_accel_time = hbk_accel_data['Epoch']

    g = 9.81
    hbk_accel_x = hbk_accel_data['FilteredAccelX']*g
    hbk_accel_y = hbk_accel_data['FilteredAccelY']*g
    hbk_accel_z = hbk_accel_data['FilteredAccelZ']*-g

    hbk_gyro_time = hbk_gyro_data['Epoch']
    hbk_gyro_x = hbk_gyro_data['FilteredGyroX']
    hbk_gyro_y = hbk_gyro_data['FilteredGyroY']
    hbk_gyro_z = hbk_gyro_data['FilteredGyroZ']

    hbk_mag_time = hbk_mag_data['Epoch']

    
    hbk_mag_x = hbk_mag_data['FilteredMagX']*emfi
    hbk_mag_y = hbk_mag_data['FilteredMagY']*emfi
    hbk_mag_z = hbk_mag_data['FilteredMagZ']*emfi

    # Now plot the comparison
    fig, axes = plt.subplots(5, 3, figsize=(15, 12))
    fig.suptitle("Comparison of Navigator and HBK IMU, Gyro, and Mag", fontsize=16)

    # Plot IMU (acceleration) comparison
    axes[0, 0].plot(hbk_accel_time, hbk_accel_x, label='HBK IMU X')
    axes[0, 0].plot(nav_data["TimeStamp"], nav_data["Imu_X"], label='Navigator IMU X', linestyle='--')
    axes[0, 0].set_title("IMU X")
    axes[0, 0].legend()

    axes[0, 1].plot(hbk_accel_time, hbk_accel_y, label='HBK IMU Y')
    axes[0, 1].plot(nav_data["TimeStamp"], nav_data["Imu_Y"], label='Navigator IMU Y', linestyle='--')
    axes[0, 1].set_title("IMU Y")
    axes[0, 1].legend()

    axes[0, 2].plot(hbk_accel_time, hbk_accel_z, label='HBK IMU Z')
    axes[0, 2].plot(nav_data["TimeStamp"], nav_data["Imu_Z"], label='Navigator IMU Z', linestyle='--')
    axes[0, 2].set_title("IMU Z")
    axes[0, 2].legend()

    # Plot Gyro comparison
    axes[1, 0].plot(hbk_gyro_time, hbk_gyro_x, label='HBK Gyro X')
    axes[1, 0].plot(nav_data["TimeStamp"], nav_data["Gyro_X"], label='Navigator Gyro X', linestyle='--')
    axes[1, 0].set_title("Gyro Z")
    axes[1, 0].legend()

    axes[1, 1].plot(hbk_gyro_time, hbk_gyro_y, label='HBK Gyro Y')
    axes[1, 1].plot(nav_data["TimeStamp"], nav_data["Gyro_Y"], label='Navigator Gyro Y', linestyle='--')
    axes[1, 1].set_title("Gyro Y")
    axes[1, 1].legend()

    axes[1, 2].plot(hbk_gyro_time, hbk_gyro_z, label='HBK Gyro Z')
    axes[1, 2].plot(nav_data["TimeStamp"], nav_data["Gyro_Z"], label='Navigator Gyro Z', linestyle='--')
    axes[1, 2].set_title("Gyro Z")
    axes[1, 2].legend()

    # Plot Magnetometer comparison
    axes[2, 0].plot(hbk_mag_time, hbk_mag_x, label='HBK Mag X')
    axes[2, 0].plot(nav_data["TimeStamp"], nav_data["Mag_1_X"], label='Navigator Mag X', linestyle='--')
    axes[2, 0].set_title("Magnetometer X")
    axes[2, 0].legend()

    axes[2, 1].plot(hbk_mag_time, hbk_mag_y, label='HBK Mag Y')
    axes[2, 1].plot(nav_data["TimeStamp"], nav_data["Mag_1_Y"], label='Navigator Mag Y', linestyle='--')
    axes[2, 1].set_title("Magnetometer Y")
    axes[2, 1].legend()

    axes[2, 2].plot(hbk_mag_time, hbk_mag_z, label='HBK Mag Z')
    axes[2, 2].plot(nav_data["TimeStamp"], nav_data["Mag_1_Z"], label='Navigator Mag Z', linestyle='--')
    axes[2, 2].set_title("Magnetometer Z")
    axes[2, 2].legend()

    # Plot Euler angles comparison
    axes[3, 0].plot(hbk_attitude_data['Epoch'], hbk_attitude_data['Roll'], label='HBK Roll')
    axes[3, 0].plot(nav_time, nav_roll, label='Navigator Roll', linestyle='--')
    axes[3, 0].set_title("Roll")
    axes[3, 0].legend()

    axes[3, 1].plot(hbk_attitude_data['Epoch'], hbk_attitude_data['Pitch'], label='HBK Pitch')
    axes[3, 1].plot(nav_time, nav_pitch, label='Navigator Pitch', linestyle='--')
    axes[3, 1].set_title("Pitch")
    axes[3, 1].legend()

    axes[3, 2].plot(hbk_attitude_data['Epoch'], hbk_attitude_data['Heading'], label='HBK Heading')
    axes[3, 2].plot(nav_time, nav_heading, label='Navigator Heading', linestyle='--')
    axes[3, 2].set_title("Heading")
    axes[3, 2].legend()


    plt.tight_layout()
    plt.savefig(output_directory + 'nav_vs_hbk.png', dpi=300, bbox_inches='tight')


    """ 
        4) We are now going to plot the GPS X/Y Track Overlay on Satellite Map
    """
    import cartopy.crs as ccrs
    import cartopy.io.img_tiles as cimgt
    import numpy as np
    import matplotlib.pyplot as plt
    from pyproj import Geod

    # Define the WGS84 ellipsoid model
    geod = Geod(ellps="WGS84")

    # Origin latitude and longitude (where X=0 and Y=0)
    LatOrigin  = 42.358456
    LongOrigin = -71.087589
    
    gps_lats = data_df_sliced['nav_lat']
    gps_lons = data_df_sliced['nav_lon']

    gps_x = data_df_sliced['nav_x_gps'].dropna().replace([np.inf, -np.inf], np.nan).dropna()
    gps_y = data_df_sliced['nav_y_gps'].dropna().replace([np.inf, -np.inf], np.nan).dropna()

    # Assuming nav_x_gps is in meters (East-West) and nav_y_gps is in meters (North-South)
    # Convert each point from Cartesian (X/Y) to Latitude/Longitude using geodesic conversion
    converted_lats = []
    converted_lons = []

    for x, y in zip(gps_x, gps_y):
        # Calculate distance and bearing from the origin based on Cartesian X/Y
        distance = np.sqrt(x**2 + y**2)  # Hypotenuse (distance in meters)
        bearing = np.degrees(np.arctan2(x, y))  # Bearing in degrees (angle from North)

        # Use Geod.fwd to calculate the new lat/lon from the origin
        lon, lat, _ = geod.fwd(LongOrigin, LatOrigin, bearing, distance)

        converted_lats.append(lat)
        converted_lons.append(lon)

    # Convert the lists to numpy arrays for plotting
    converted_lats = np.array(converted_lats)
    converted_lons = np.array(converted_lons)

    # Define map projection
    print("Plotting GPS X/Y Track Overlay on Satellite Map")
    fig = plt.figure(figsize=(10, 10))  # Square figure
    ax = plt.axes(projection=ccrs.PlateCarree())

    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    compass_rose_path = os.path.expanduser('~/moos/moos-ivp-seascout/assets/graphics/compass_rose.png')

    # Use ESRI World Imagery as the background
    # esri_imagery = cimgt.QuadtreeTiles()
    # ax.add_image(esri_imagery, 20)  # Zoom level 20 for high detail
    # stamen_terrain = cimgt.Stamen('terrain')
    # ax.add_image(stamen_terrain, 10)  # Zoom level 10 for street map style
    openstreetmap = cimgt.OSM()
    ax.add_image(openstreetmap, 18)  # Adjust zoom level if necessary

    # Plot the converted latitude/longitude track
    ax.plot(converted_lons, converted_lats, marker='o', color='blue', transform=ccrs.PlateCarree(), label="GPS X/Y Converted Track")
    ax.plot(gps_lons, gps_lats, marker='o', color='red', transform=ccrs.PlateCarree(), label="GPS X/Y Converted Track")

    # Optionally add labels
    ax.set_title('GPS X/Y Track Overlay on Satellite Map')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Set extent based on the new lat/lon values

    # Calculate the range of latitude and longitude to determine the zoom
    lat_range = converted_lats.max() - converted_lats.min()
    lon_range = converted_lons.max() - converted_lons.min()

    # Find the larger range to keep the plot square and add 20% padding
    max_range = max(lat_range, lon_range)
    padding = max_range * 1.5
    lat_min, lat_max = converted_lats.min() - padding, converted_lats.max() + padding
    lon_min, lon_max = converted_lons.min() - padding, converted_lons.max() + padding

    ax.set_extent([lon_min, lon_max, lat_min, lat_max])

    # Add a grid
    ax.gridlines(draw_labels=True)
    compass_image = plt.imread(compass_rose_path)

    # Create an offset box for the compass rose
    imagebox = OffsetImage(compass_image, zoom=0.3)  # Adjust the zoom to control the size

    # Position the compass rose in the top-right corner of the plot (normalized coordinates: 1.05, 0.95)
    xy = (0.85, 0.85)  # (x, y) location in normalized coordinates
    ab = AnnotationBbox(imagebox, xy, xycoords='axes fraction', frameon=False)

    # Add the annotation box to the axis
    ax.add_artist(ab)

    # Save the figure
    plt.savefig(output_directory + 'gps_xy_track_satellite_esri_converted.png', dpi=300, bbox_inches='tight')

    """

    5) Basic DVL Data Analysis to see what is going on
    We are going to make plots for the dvl data

    pdx
    timeSinceEpoch,utimeSinceBoot,duT,angleDeltaRoll,angleDeltaPitch,angleDeltaYaw,deltaX,deltaY,deltaZ,latestConfidence,mode,pitch,roll,yaw,standoff,valid

    kfc
    timeSinceEpoch,id,seq,dt,tod,channelA_cg,channelA_pc,channelA_ra,channelA_rc,channelA_vv,channelA_vc,channelB_cg,channelB_pc,channelB_ra,channelB_rc,channelB_vv,channelB_vc,channelC_cg,channelC_pc,channelC_ra,channelC_rc,channelC_vv,channelC_vc,endOfMessageTag
    """


    # Process the DVL data to get what we want to analyze and compare w/rt to other data we have

    dvl_pdx_data['timeSinceEpoch'] = dvl_pdx_data['timeSinceEpoch'] - log_start
    dvl_pdx_data['time'] = dvl_pdx_data['timeSinceEpoch']
    dvl_pdx_data.set_index('time', inplace=True)

    slc = (dvl_pdx_data['timeSinceEpoch'] <= (t_end + t_window_post)) & (dvl_pdx_data['timeSinceEpoch'] >= (t_start - t_window_pre))
    dvl_pdx_data = dvl_pdx_data[slc]

    dvl_pdx_data['dT'] = dvl_pdx_data['duT']/1000000

    dvl_pdx_data['surge'] = dvl_pdx_data['deltaX']/dvl_pdx_data['dT']
    dvl_pdx_data['sway'] = dvl_pdx_data['deltaY']/dvl_pdx_data['dT']
    dvl_pdx_data['heave'] = dvl_pdx_data['deltaZ']/dvl_pdx_data['dT']
    dvl_pdx_data['mask'] = ~dvl_pdx_data['deltaX'].isna()

    dvl_pdx_data.drop(columns=['duT', 'deltaX', 'deltaY', 'deltaZ'], inplace=True)

    # Join DVL and navigator data on 'timeSinceEpoch', forward-fill all columns except 'mask'
    dvl_pdx_rt_data = dvl_pdx_data.join(nav_data[['Roll', 'Pitch', 'Yaw', 'Heading']], how='left')
    dvl_pdx_rt_data[['Roll', 'Pitch', 'Yaw', 'Heading']] = dvl_pdx_rt_data[['Roll', 'Pitch', 'Yaw', 'Heading']].fillna(method='ffill')

    # Drop rows with NaN in DVL columns (identified by 'mask' column)
    dvl_pdx_rt_data = dvl_pdx_rt_data.loc[dvl_pdx_rt_data['mask']]

    # Convert Roll, Pitch, and Heading to radians
    dvl_pdx_rt_data['roll_rad'] = np.radians(dvl_pdx_rt_data['Roll'])
    dvl_pdx_rt_data['pitch_rad'] = np.radians(dvl_pdx_rt_data['Pitch'])
    dvl_pdx_rt_data['heading_cart_rad'] = np.radians(450 - dvl_pdx_rt_data['Heading']) % (2 * np.pi) 

    # Define rotation matrices using heading (yaw replacement), pitch, and roll
    def rotation_matrix(roll, pitch, heading):
        R_x = np.array([[1, 0, 0],
                        [0, np.cos(roll), -np.sin(roll)],
                        [0, np.sin(roll), np.cos(roll)]])
        
        R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                        [0, 1, 0],
                        [-np.sin(pitch), 0, np.cos(pitch)]])
        
        heading = heading + 4.5*np.pi/180.0
        R_z = np.array([[np.cos(heading), -np.sin(heading), 0],
                        [np.sin(heading), np.cos(heading), 0],
                        [0, 0, 1]])
        
        return R_z @ R_y @ R_x

    # Apply rotation matrix to get x_dot, y_dot, z_dot in world frame
    def transform_to_world(row):
        R = rotation_matrix(row['roll_rad'], row['pitch_rad'], row['heading_cart_rad'])
        local_velocity = np.array([row['surge'], row['sway'], row['heave']])
        world_velocity = R @ local_velocity
        return world_velocity

    # Calculate world frame velocities
    dvl_pdx_rt_data[['x_dot', 'y_dot', 'z_dot']] = pd.DataFrame(
        dvl_pdx_rt_data.apply(transform_to_world, axis=1).tolist(),
        index=dvl_pdx_rt_data.index
    )

    # Join and synchronize all the data with feed forward 
    dvl_pdx_rt_data = dvl_pdx_rt_data.join(data_df_sliced[['nav_x_gps', 'nav_y_gps', 'in_water']], how='outer')
    
    # Forward fill all columns except the mask to preserve the actual measured values
    columns_to_ffill = list(dvl_pdx_rt_data.columns )
    columns_to_ffill.remove('mask')
    dvl_pdx_rt_data[columns_to_ffill] = dvl_pdx_rt_data[columns_to_ffill].fillna(method='ffill')

    # Since we filled outer and time stamps weren't exact, many NaN values from the data_df_sliced dataframe 
    dvl_pdx_rt_data.dropna(inplace=True)

    # Since we preserved the mask, drop all non-mask values
    dvl_pdx_rt_data = dvl_pdx_rt_data.loc[dvl_pdx_rt_data['mask']]

    # Get the first row where 'in_water' is True
    first_in_water_row = dvl_pdx_rt_data[dvl_pdx_rt_data['in_water']].iloc[0]

    # Extract the starting x and y GPS positions
    start_nav_x_gps = first_in_water_row['nav_x_gps']
    start_nav_y_gps = first_in_water_row['nav_y_gps']
    start_z = 0
    dvl_pdx_rt_data['dt'] = dvl_pdx_rt_data.index.to_series().diff().fillna(0)  # Time differences between rows

    # Step 2: Compute the deltas for x, y, and z using world-frame velocities
    dvl_pdx_rt_data['delta_x'] = dvl_pdx_rt_data['x_dot'] * dvl_pdx_rt_data['dt']
    dvl_pdx_rt_data['delta_y'] = dvl_pdx_rt_data['y_dot'] * dvl_pdx_rt_data['dt']
    dvl_pdx_rt_data['delta_z'] = dvl_pdx_rt_data['z_dot'] * dvl_pdx_rt_data['dt']

    # Step 3: Cumulative sum of deltas to propagate the positions
    dvl_pdx_rt_data['x_prop'] = dvl_pdx_rt_data['delta_x'].cumsum() + start_nav_x_gps
    dvl_pdx_rt_data['y_prop'] = dvl_pdx_rt_data['delta_y'].cumsum() + start_nav_y_gps
    dvl_pdx_rt_data['z_prop'] = dvl_pdx_rt_data['delta_z'].cumsum() + start_z

    dvl_pdx_rt_data['t_mission'] = dvl_pdx_rt_data['timeSinceEpoch'] - dvl_pdx_rt_data['timeSinceEpoch'].iloc[0]

    # Set up the figure with multiple subplots
    rs = 9
    cs = 2
    fig = plt.figure(figsize=(12, 18))

    # Plot 1: Surge, Sway, Heave
    ax = plt.subplot2grid((rs, cs), (0, 0), rowspan=2, colspan=1)
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['surge'], label='Surge')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['sway'], label='Sway')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['heave'], label='Heave')
    ax.set_title('Surge, Sway, Heave')
    ax.set_xlabel('Time')
    ax.set_ylabel('Velocity (m/s)')
    ax.legend()
    ax.grid(True)

    # Plot 2: Roll, Pitch, Yaw/Heading
    ax = plt.subplot2grid((rs, cs), (2, 0), rowspan=2, colspan=1)
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['Roll'], label='Roll')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['Pitch'], label='Pitch')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['Heading'], label='Heading')
    ax.set_title('Roll, Pitch, Yaw/Heading (Degrees)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Angle (Degrees)')
    ax.legend()
    ax.grid(True)

    # Plot 3: x_dot, y_dot, z_dot
    ax = plt.subplot2grid((rs, cs), (4, 0), rowspan=2, colspan=1)
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['x_dot'], label='X_dot')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['y_dot'], label='Y_dot')
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['z_dot'], label='Z_dot')
    ax.set_title('X_dot, Y_dot, Z_dot (World Frame Velocities)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Velocity (m/s)')
    ax.legend()
    ax.grid(True)

    # Plot 4: Depth
    ax = plt.subplot2grid((rs, cs), (6, 0), rowspan=2, colspan=1)
    ax.plot(data_df_sliced['t'], -data_df_sliced['nav_depth'],color='green',label='Depth')
    ax.set_title('Depth')
    ax.set_xlabel('Time')
    ax.set_ylabel('Depth (m)')
    ax.legend()
    ax.grid(True)

    # Plot 5: Standoff
    ax = plt.subplot2grid((rs, cs), (0, 1), rowspan=2, colspan=1)
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['standoff'], label='Standoff')
    ax.set_title('Standoff')
    ax.set_xlabel('Time')
    ax.set_ylabel('Standoff (m)')
    ax.legend()
    ax.grid(True)

    # Plot 6: Confidence
    ax = plt.subplot2grid((rs, cs), (2, 1), rowspan=2, colspan=1)
    ax.plot(dvl_pdx_rt_data.index, dvl_pdx_rt_data['latestConfidence'], label='Confidence')
    ax.set_title('Confidence')
    ax.set_xlabel('Time')
    ax.set_ylabel('Confidence')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(output_directory + 'dvl_basic.png', dpi=300, bbox_inches='tight')

    """ 
        6) Side by side trajectory comparison
    """
    # Set up a new figure with two subplots (side by side)
    fig, (ax_dvl, ax_unit) = plt.subplots(1, 2, figsize=(12, 6), constrained_layout=True)

    # DVL Propagated X/Y positions
    sc_dvl = ax_dvl.scatter(dvl_pdx_rt_data['x_prop'], dvl_pdx_rt_data['y_prop'], 
                            c=dvl_pdx_rt_data['t_mission'], cmap='viridis', label='Propagated X/Y', marker='o')

    # Plot the starting point for reference in DVL
    ax_dvl.scatter(start_nav_x_gps, start_nav_y_gps, color='red', label='Start Position', zorder=5)

    # DVL plot titles and labels
    ax_dvl.set_title('DVL Propagated X/Y Positions')
    ax_dvl.set_xlabel('X Position (m)')
    ax_dvl.set_ylabel('Y Position (m)')
    ax_dvl.legend()
    ax_dvl.grid(True)

    # Add colorbar for the DVL plot
    cbar_dvl = plt.colorbar(sc_dvl, ax=ax_dvl)
    cbar_dvl.set_label('Time')

    # Unit Trajectory X/Y (replace `x_sim` and `y_sim` with the variables used in your unit trajectory)
    sc_unit = ax_unit.scatter(data_df_sliced_traj['x_sim'], data_df_sliced_traj['y_sim'], 
                            c=data_df_sliced_traj['t_mission'], cmap='plasma', label='Unit Trajectory', marker='o')

    # Unit Trajectory plot titles and labels
    ax_unit.set_title('Unit Trajectory X/Y Positions')
    ax_unit.set_xlabel('X Position (m)')
    ax_unit.set_ylabel('Y Position (m)')
    ax_unit.legend()
    ax_unit.grid(True)

    # Add colorbar for the Unit Trajectory plot
    cbar_unit = plt.colorbar(sc_unit, ax=ax_unit)
    cbar_unit.set_label('Time')

    # Save the combined figure with both plots
    plt.savefig(output_directory + 'dvl_vs_unit_xy_trajectory.png', dpi=300, bbox_inches='tight')


    """ 
        7) Now we are going to naively plot the propagated X/Y velocities using the AHRS and the DVL measurements vs GPS X/Y
    """
    fig_xy = plt.figure(figsize=(10, 10))

    # Define the WGS84 ellipsoid model
    geod = Geod(ellps="WGS84")

    # Origin latitude and longitude (where X=0 and Y=0)
    LatOrigin = 42.358456
    LongOrigin = -71.087589

    gps_lats = data_df_sliced['nav_lat']
    gps_lons = data_df_sliced['nav_lon']

    # Convert propagated X/Y into lat/lon
    propagated_lats = []
    propagated_lons = []

    for x, y in zip(dvl_pdx_rt_data['x_prop'], dvl_pdx_rt_data['y_prop']):
        distance = np.sqrt(x**2 + y**2)  # Calculate distance in meters
        bearing = np.degrees(np.arctan2(x, y))  # Calculate bearing in degrees

        # Convert the X/Y to lat/lon from the origin
        lon, lat, _ = geod.fwd(LongOrigin, LatOrigin, bearing, distance)

        propagated_lats.append(lat)
        propagated_lons.append(lon)

    propagated_lats = np.array(propagated_lats)
    propagated_lons = np.array(propagated_lons)

    # Plot both the GPS and propagated data on the same map
    fig = plt.figure(figsize=(10, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Use OpenStreetMap as background
    openstreetmap = cimgt.OSM()
    ax.add_image(openstreetmap, 18)

    # Plot propagated data
    ax.scatter(propagated_lons, propagated_lats, marker='o', color='blue', transform=ccrs.PlateCarree(), label="Propagated X/Y")

    # Plot GPS data
    ax.scatter(gps_lons, gps_lats, marker='o', color='red', transform=ccrs.PlateCarree(), label="GPS X/Y")

    # Set extent based on the new lat/lon values
    lat_range = propagated_lats.max() - propagated_lats.min()
    lon_range = propagated_lons.max() - propagated_lons.min()
    max_range = max(lat_range, lon_range)
    padding = max_range * 1.5  # Add 25% padding
    ax.set_extent([propagated_lons.min() - padding, propagated_lons.max() + padding,
                propagated_lats.min() - padding, propagated_lats.max() + padding])
                
    # Optionally, add labels and styling
    ax.set_title('Propagated X/Y vs GPS X/Y')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.gridlines(draw_labels=True)

    # Add the compass rose
    compass_image = plt.imread(compass_rose_path)
    imagebox = OffsetImage(compass_image, zoom=0.3)
    xy = (0.85, 0.85)
    ab = AnnotationBbox(imagebox, xy, xycoords='axes fraction', frameon=False)
    ax.add_artist(ab)

    # Save the figure
    plt.tight_layout()
    plt.savefig(output_directory + 'propagated_vs_gps_map.png', dpi=300, bbox_inches='tight')

    # Initialize the WGS84 ellipsoid model
    from pyproj import Geod
    geod = Geod(ellps="WGS84")

    # Origin latitude and longitude (where X=0 and Y=0)
    LatOrigin = 42.358456
    LongOrigin = -71.087589

    # Sample data for GPS lats/lons (from data_df_sliced)
    gps_lats = data_df_sliced['nav_lat'].values
    gps_lons = data_df_sliced['nav_lon'].values

    # Convert propagated X/Y into lat/lon coordinates
    propagated_lats = []
    propagated_lons = []

    for x, y in zip(dvl_pdx_rt_data['x_prop'], dvl_pdx_rt_data['y_prop']):
        distance = np.sqrt(x**2 + y**2)  # Calculate distance in meters
        bearing = np.degrees(np.arctan2(x, y))  # Calculate bearing in degrees

        # Convert X/Y to lat/lon from the origin using pyproj's Geod.fwd method
        lon, lat, _ = geod.fwd(LongOrigin, LatOrigin, bearing, distance)
        propagated_lats.append(lat)
        propagated_lons.append(lon)

    # Convert lists to numpy arrays for easy plotting
    propagated_lats = np.array(propagated_lats)
    propagated_lons = np.array(propagated_lons)

    # print the nav_x_gps and nav_y_gps, vs. propagated x and y
    print(f"GPS: ({gps_x.iloc[-1]}, {gps_y.iloc[-1]}), DVL: ({dvl_pdx_rt_data['x_prop'].iloc[-1]}, {dvl_pdx_rt_data['y_prop'].iloc[-1]})")

    # print the error between the two
    error_x = gps_x.iloc[-1] - dvl_pdx_rt_data['x_prop'].iloc[-1]
    error_y = gps_y.iloc[-1] - dvl_pdx_rt_data['y_prop'].iloc[-1]
    print(f"Error: ({error_x}, {error_y})")
    # eucl distance
    eucl_dist = np.sqrt(error_x**2 + error_y**2)
    print(f"Euclidean Distance: {eucl_dist}")

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 10))

    

    # Plot the propagated X/Y data in blue
    ax.scatter(propagated_lons, propagated_lats, marker='o', color='blue', linestyle='-', label="Propagated X/Y")

    # Plot the GPS data in red
    ax.scatter(gps_lons, gps_lats, marker='o', color='red', linestyle='-', label="GPS X/Y")

    # Set title, labels, and equal aspect ratio
    ax.set_title('Propagated X/Y vs GPS X/Y')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_aspect('equal', adjustable='datalim')
    ax.legend()
    ax.grid(True)

    # Calculate extent with 15% padding
    lat_padding = (propagated_lats.max() - propagated_lats.min()) * 0.15
    lon_padding = (propagated_lons.max() - propagated_lons.min()) * 0.15
    ax.set_xlim(propagated_lons.min() - lon_padding, propagated_lons.max() + lon_padding)
    ax.set_ylim(propagated_lats.min() - lat_padding, propagated_lats.max() + lat_padding)

    # Set compass rose path using SEASCOUT_PATH environment variable
    seascout_path = os.getenv('SEASCOUT_PATH', '')
    from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    compass_rose_path = os.path.join(seascout_path, 'assets', 'graphics', 'compass_rose.png')
    compass_image = plt.imread(compass_rose_path)
    imagebox = OffsetImage(compass_image, zoom=0.3)
    xy = (0.85, 0.85)  # Normalized coordinates for positioning
    ab = AnnotationBbox(imagebox, xy, xycoords='axes fraction', frameon=False)
    ax.add_artist(ab)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_directory + 'propagated_vs_gps_no_cartopy.png', dpi=300, bbox_inches='tight')