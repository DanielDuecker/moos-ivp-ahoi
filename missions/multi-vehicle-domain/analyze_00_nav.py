#!/bin/python3

import sys
import os
import json 
import glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

def rotation_matrix(roll, pitch, heading, heading_offset_deg=4.5):
    """Create rotation matrix with optional heading offset"""
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(roll), -np.sin(roll)],
                    [0, np.sin(roll), np.cos(roll)]])
    
    R_y = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                    [0, 1, 0],
                    [-np.sin(pitch), 0, np.cos(pitch)]])
    
    heading = heading + heading_offset_deg*np.pi/180.0
    R_z = np.array([[np.cos(heading), -np.sin(heading), 0],
                    [np.sin(heading), np.cos(heading), 0],
                    [0, 0, 1]])
    
    return R_z @ R_y @ R_x

def transform_to_world(row, heading_offset_deg=4.5):
    """Transform body velocities to world frame"""
    R = rotation_matrix(row['roll_rad'], row['pitch_rad'], row['heading_cart_rad'], heading_offset_deg)
    local_velocity = np.array([row['surge'], row['sway'], row['heave']])
    return R @ local_velocity

def main():
    # Get mission directory from command line argument
    mission_directory = sys.argv[1]
    #heading_offset = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5  # Default offset of 4.5 degrees
    heading_offset = 0
    
    # Set up output directory
    output_directory = f"{mission_directory}_meta/"
    os.makedirs(output_directory, exist_ok=True)
    
    # Load mission data
    glb = glob.glob(f"{mission_directory}/*_tmp/*whole.json")
    mission_data = json.load(open(glb[0]))
    mission = next(iter(mission_data))
    
    # Extract relevant data fields
    info = mission_data[mission]['info']
    log_start = info["logstart"]
    raw_data = mission_data[mission]['data']
    
    def cast(dat, var):
        var = var.lower()
        if var == "f":
            return float(dat)
        elif var == "s":
            return str(dat)
    
    # Create DataFrames for each measurement type
    all_data = []
    data_fields = {
        'NAV_X': 'f',
        'NAV_Y': 'f',
        'NAV_X_GPS': 'f',
        'NAV_Y_GPS': 'f',
        'IN_WATER': 's',
        'MISSION_COMPLETE': 's',
        'NAV_ENGINE_STATE': 's'
    }
    
    for k, v in data_fields.items():
        if k in raw_data:
            set = [[entry[0]-log_start, cast(entry[1], v)] for entry in raw_data[k]]
            df = pd.DataFrame(set, columns=["time", k.lower()]).set_index("time")
            all_data.append(df)
    
    # Combine all data
    data_df = all_data.pop()
    for elem in all_data:
        data_df = data_df.join(elem, how='outer')
    
    # Process boolean columns
    data_df["in_water"] = data_df['in_water'].fillna("false").map({'true': True, 'false': False})
    data_df["mission_complete"] = data_df['mission_complete'].fillna("false").map({'true': True, 'false': False})
    
    # Fill missing values and clean data
    data_df.fillna(method='ffill', inplace=True)
    data_df.dropna(inplace=True)
    
    # Get mission start and end times
    mission_start_index = data_df['in_water'].idxmax()
    mission_complete_index = data_df['mission_complete'].idxmax()
    
    # Filter data to mission duration plus margins
    margin = 20  # seconds
    mask = (data_df.index <= mission_complete_index + margin) & (data_df.index >= mission_start_index - margin)
    data_df_filtered = data_df[mask]
    
    # Create t_mission variable
    data_df_filtered['t_mission'] = data_df_filtered.index - mission_start_index

    # Load Navigator AHRS and DVL data
    nav_ahrs_file = glob.glob(f"{mission_directory}/*_Navigator_AHRS.csv")[0]
    dvl_pdx_file = glob.glob(f"{mission_directory}/*_Tracker650_PDX.csv")[0]
    
    # Read and process Navigator data
    nav_data = pd.read_csv(nav_ahrs_file)
    nav_data['TimeStamp'] = nav_data['TimeStamp'] - log_start
    nav_data["t"] = nav_data['TimeStamp']
    nav_data.set_index('t', inplace=True)
    
    # Read and process DVL data
    dvl_pdx_data = pd.read_csv(dvl_pdx_file)
    dvl_pdx_data.drop(columns=['angleDeltaRoll', 'angleDeltaPitch', 'angleDeltaYaw'], inplace=True)
    dvl_pdx_data['timeSinceEpoch'] = dvl_pdx_data['timeSinceEpoch'] - log_start
    dvl_pdx_data['time'] = dvl_pdx_data['timeSinceEpoch']
    dvl_pdx_data.set_index('time', inplace=True)
    
    # Apply time slicing to nav and DVL data
    nav_data = nav_data[(nav_data.index <= mission_complete_index + margin) & 
                        (nav_data.index >= mission_start_index - margin)]
    dvl_pdx_data = dvl_pdx_data[(dvl_pdx_data.index <= mission_complete_index + margin) & 
                                (dvl_pdx_data.index >= mission_start_index - margin)]
    
    # Process DVL measurements
    dvl_pdx_data['dT'] = dvl_pdx_data['duT']/1000000
    dvl_pdx_data['surge'] = dvl_pdx_data['deltaX']/dvl_pdx_data['dT']
    dvl_pdx_data['sway'] = dvl_pdx_data['deltaY']/dvl_pdx_data['dT']
    dvl_pdx_data['heave'] = dvl_pdx_data['deltaZ']/dvl_pdx_data['dT']
    dvl_pdx_data['mask'] = ~dvl_pdx_data['deltaX'].isna()
    
    # Join DVL and navigator data
    dvl_pdx_rt_data = dvl_pdx_data.join(nav_data[['Roll', 'Pitch', 'Yaw', 'Heading']], how='left')
    dvl_pdx_rt_data[['Roll', 'Pitch', 'Yaw', 'Heading']] = dvl_pdx_rt_data[['Roll', 'Pitch', 'Yaw', 'Heading']].fillna(method='ffill')
    
    # Drop rows with NaN in DVL columns
    dvl_pdx_rt_data = dvl_pdx_rt_data.loc[dvl_pdx_rt_data['mask']]
    
    # Convert angles to radians
    dvl_pdx_rt_data['roll_rad'] = np.radians(dvl_pdx_rt_data['Roll'])
    dvl_pdx_rt_data['pitch_rad'] = np.radians(dvl_pdx_rt_data['Pitch'])
    dvl_pdx_rt_data['heading_cart_rad'] = np.radians(450 - dvl_pdx_rt_data['Heading']) % (2 * np.pi)
    
    # Calculate world frame velocities
    dvl_pdx_rt_data[['x_dot', 'y_dot', 'z_dot']] = pd.DataFrame(
        dvl_pdx_rt_data.apply(lambda row: transform_to_world(row, heading_offset), axis=1).tolist(),
        index=dvl_pdx_rt_data.index
    )

    # Get starting position from first valid GPS point
    first_gps = data_df_filtered.loc[~data_df_filtered['nav_x_gps'].isna()].iloc[0]
    start_nav_x_gps = first_gps['nav_x_gps']
    start_nav_y_gps = first_gps['nav_y_gps']
    
    # Propagate position
    dvl_pdx_rt_data['dt'] = dvl_pdx_rt_data.index.to_series().diff().fillna(0)
    dvl_pdx_rt_data['delta_x'] = dvl_pdx_rt_data['x_dot'] * dvl_pdx_rt_data['dt']
    dvl_pdx_rt_data['delta_y'] = dvl_pdx_rt_data['y_dot'] * dvl_pdx_rt_data['dt']
    dvl_pdx_rt_data['x_prop'] = dvl_pdx_rt_data['delta_x'].cumsum() + start_nav_x_gps
    dvl_pdx_rt_data['y_prop'] = dvl_pdx_rt_data['delta_y'].cumsum() + start_nav_y_gps
    
    dvl_pdx_rt_data['t_mission'] = dvl_pdx_rt_data.index - mission_start_index
    
    # Create comparison plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # First plot: NAV vs GPS
    sc1 = ax1.scatter(data_df_filtered['nav_x'], data_df_filtered['nav_y'], 
                     c=data_df_filtered['t_mission'], cmap='viridis', 
                     marker='^', s=10, label='NAV Position')
    
    sc2 = ax1.scatter(data_df_filtered['nav_x_gps'], data_df_filtered['nav_y_gps'], 
                     c=data_df_filtered['t_mission'], cmap='plasma', 
                     marker='o', edgecolors='black',
                     s=10, label='GPS Position')
    
    gps_fixing_mask = data_df_filtered['nav_engine_state'] == 'GPS_FIXING'
    if gps_fixing_mask.any():
        ax1.scatter(data_df_filtered.loc[gps_fixing_mask, 'nav_x'], 
                   data_df_filtered.loc[gps_fixing_mask, 'nav_y'],
                   marker='o', s=300, facecolors='none',
                   edgecolors='orange', linewidths=0.5,
                   alpha=0.2, label='GPS Fix')
    
    ax1.set_title('Navigation vs GPS Position')
    ax1.set_xlabel('X Position (m)')
    ax1.set_aspect('equal')
    ax1.set_ylabel('Y Position (m)')
    ax1.legend()
    ax1.grid(True)
    ax1.axis('equal')
    
    # Second plot: DVL Propagation vs GPS
    sc3 = ax2.scatter(dvl_pdx_rt_data['x_prop'], dvl_pdx_rt_data['y_prop'],
                     c=dvl_pdx_rt_data['t_mission'], cmap='viridis',
                     marker='^', s=10, label=f'DVL Prop (offset={heading_offset}°)')
    
    sc4 = ax2.scatter(data_df_filtered['nav_x_gps'], data_df_filtered['nav_y_gps'],
                     c=data_df_filtered['t_mission'], cmap='plasma',
                     marker='o', edgecolors='black',
                     s=10, label='GPS Position')
    
    ax2.set_title('DVL Propagation vs GPS Position')
    ax2.set_xlabel('X Position (m)')
    ax2.set_ylabel('Y Position (m)')
    ax2.set_aspect('equal')
    ax2.legend()
    ax2.grid(True)
    ax2.axis('equal')
    
    # Add colorbars
    plt.colorbar(sc1, ax=ax1, label='Mission Time (s)')
    plt.colorbar(sc3, ax=ax2, label='Mission Time (s)')
    
    plt.tight_layout()
    plt.savefig(output_directory + f'trajectory_comparison_offset_{heading_offset}.png', dpi=300, bbox_inches='tight')

    # Calculate total odometry and average speed for DVL propagated trajectory
    dvl_pdx_rt_data['delta_dist'] = np.sqrt(dvl_pdx_rt_data['delta_x']**2 + dvl_pdx_rt_data['delta_y']**2)
    dvl_total_odometry = dvl_pdx_rt_data['delta_dist'].sum()
    dvl_total_time = dvl_pdx_rt_data['dt'].sum()
    dvl_average_speed = dvl_total_odometry / dvl_total_time if dvl_total_time > 0 else 0

    # Calculate total odometry and average speed for navigation solution
    data_df_filtered['nav_delta_x'] = data_df_filtered['nav_x'].diff()
    data_df_filtered['nav_delta_y'] = data_df_filtered['nav_y'].diff()
    data_df_filtered['nav_delta_dist'] = np.sqrt(data_df_filtered['nav_delta_x']**2 + data_df_filtered['nav_delta_y']**2)
    data_df_filtered['nav_dt'] = data_df_filtered.index.to_series().diff()
    nav_total_odometry = data_df_filtered['nav_delta_dist'].sum()
    nav_total_time = data_df_filtered['nav_dt'].sum()
    nav_average_speed = nav_total_odometry / nav_total_time if nav_total_time > 0 else 0

    print(f"\nDVL Propagated Trajectory Statistics:")
    print(f"Total Distance Traveled: {dvl_total_odometry:.2f} meters")
    print(f"Total Time: {dvl_total_time:.2f} seconds") 
    print(f"Average Speed: {dvl_average_speed:.2f} m/s")

    print(f"\nNavigation Solution Statistics:")
    print(f"Total Distance Traveled: {nav_total_odometry:.2f} meters")
    print(f"Total Time: {nav_total_time:.2f} seconds") 
    print(f"Average Speed: {nav_average_speed:.2f} m/s")

if __name__ == "__main__":
    main()