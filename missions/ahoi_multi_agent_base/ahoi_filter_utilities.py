import numpy as np
import pandas as pd
import datetime


class AnchorEstimator():
    def __init__(self, anchor_id_list) -> None:
        self._anchor_id_list = anchor_id_list
        self._anchor_dict= {}
        for anchor_id in anchor_id_list:
            self._anchor_dict[anchor_id] = AnchorEstModel(anchor_id)
        
    def get_anchor(self,anchor_id):
        return self._anchor_dict[anchor_id]

class AnchorEstModel():
    def __init__(self, id, logging=False) -> None:
        self._id = id
        self._logging = logging

        self._log_pos = []
        self._log_range = []
        
        self._is_fully_initialized = False
        self._last_pos_time = None
        self._last_pos_poll_time = None

        self._pos = np.zeros((2,1))
        self._vel = np.zeros((2,1))

        self._last_range_time = None
        self._last_range = None

        self._number_pos_updates = 0
        self._number_range_updates = 0
    
    def get_id(self):
        return self._id 
    
    def got_range(self, range_data, timestamp):
        self._last_range = range_data
        self._last_range_time = timestamp
        self._number_range_updates += 1
        if self._logging:
            self._log_range.append((timestamp, range_data))
    
    def sent_pos_poll(self, timestamp):
        self._last_pos_poll_time = timestamp

    def update_pos(self, pos, timestamp):
        self._pos = pos
        self._last_pos_time = timestamp
        self._number_pos_updates += 1
        self._is_fully_initialized = True
        if self._logging:
            self._log_pos.append((timestamp, pos))

    def get_last_pos(self):
        if self._last_pos_time is None:
            print(f'ERROR: Anchor Pos is {self._pos} and has not been set yet for this anchor') 
        return self._pos, self, self._last_pos_time
    
    def is_valid(self):
        return self._is_fully_initialized
    
    def get_pos_age(self, current_datetime):
        # return the time since the last update
        # output in seconds
        if self._last_pos_time is None:
            print(f'ERROR: Anchor Pos is {self._pos} and has not been set yet for this anchor')
            return None, None
        pos_age = (current_datetime - self._last_pos_time).total_seconds()
        #range_age = (current_datetime - self._last_range_time).total_seconds()
        return pos_age #, range_age    

    def get_log_pos(self):
        # output list of tuples (timestamp, pos)
        return self._log_pos
    
    def get_log_range(self):
        # output list of tuples (timestamp, range)
        return self._log_range

    def comp_vel(self, pos, time):
        if self._last_pos_time is not None:
            dt = (time - self._last_pos_time).total_seconds()
            self._vel = (pos - self._pos) / dt
        else:
            self._vel = np.zeros((2,1))
        return self._vel



class AhoiMeasurement():
    def __init__(self):
        self.status = {0: 'inactive', 1: 'TOF-poll', 2: 'got_only_tof', 3: 'got_only_pos', 4:'got_tof_pos'}


        self.reset()

    def reset(self):

        self.open_poll_tof = False
        self.open_poll_pos = False

        #self.measurement_status = self.status[0] # inactive
        #self.meas_complete = False

        self.poll_time = None
        self.seq_id = None
        self.anchor_id = None

        self.rec_range = None
        self.rec_range_time = None

        self.rec_anchor_pos = None
        self.rec_pos_time = None

    def issued_poll(self, poll_type, poll_time, seq_id, anchor_id):
        if poll_type == 'TOF-poll':
            self.open_poll_tof = True
        elif poll_type == 'TOF-POS-poll':
            self.open_poll_tof = True
            self.open_poll_pos = True
        else:
            print("ERROR: Poll type not recognized")

        self.poll_time = poll_time
        self.seq_id = seq_id
        self.anchor_id = anchor_id

        self.measurement_status = self.status[1] # polled

    def get_poll_status(self):
        # return status on tof poll , pos poll
        return self.open_poll_tof, self.open_poll_pos
    
    def got_range(self):
        if self.rec_range is None:
            return False
        else:
            return True
    
    def got_pos(self):
        if self.rec_anchor_pos is None:
            return False
        else:
            return True
        
    def received_range(self, rec_range, rec_range_time, seq_i):
        if self.seq_id == seq_i:
            self.rec_range = rec_range
            self.rec_range_time = rec_range_time

            self.open_poll_tof = False # close the tof poll
            #self.measurement_status = self.status[2] # 'got_only_tof'

        else:
            print("Overlapping sequences")
    
    def received_pos(self, rec_pos, rec_pos_time, seq_i):
        if self.seq_id == seq_i:
            self.rec_anchor_pos = rec_pos
            self.rec_pos_time = rec_pos_time

            self.open_poll_pos = False # close the pos poll


            # if self.measurement_status == 'got_only_tof':
            #     self.measurement_status = self.status[4] # 'got_tof_pos'
            # else:
            #     self.measurement_status = self.status[3] # 'got_only_pos'
            # self.meas_complete = (self.rec_range is not None and self.rec_anchor_pos is not None)
        else:
            print("Overlapping sequences")

    # def is_complete(self):
    #     if self.measurement_status == 'got_tof_pos':
    #         return True
    #     else:
    #         return False

    def get_range(self):
        if self.rec_range == None:
            print(f'ERROR: Anchor Range is {self.rec_range} and has not been set yet for this sequence')
        return self.rec_range, self.anchor_id
    
    def get_anchor_pos(self):
        if self.rec_anchor_pos is None:
            print(f'ERROR: Anchor Pos is {self.rec_anchor_pos} and has not been set yet for this sequence')
        return self.rec_anchor_pos, self.anchor_id
    

class RealWorldDataLoader():
    def __init__(self,
                 ahoi_csv='2024-08-05_01_mobile_node/ahoi_interface_log_20240805_190152.csv',
                 mobile_csv='2024-08-05_01_mdm/LOG_OAK_5_8_2024_____18_34_20/log_oak_5_8_2024_____18_34_20_alog_csvs/NODE_REPORT_LOCAL.csv', 
                 id2_csv='2024-08-05_01_mdm/LOG_NED_5_8_2024_____18_34_13/log_ned_5_8_2024_____18_34_13_alog_csvs/NODE_REPORT_LOCAL.csv',
                 id6_csv='2024-08-05_01_mdm/LOG_ABE_5_8_2024_____18_34_05/log_abe_5_8_2024_____18_34_05_alog_csvs/NODE_REPORT_LOCAL.csv', 
                 id9_csv='2024-08-05_01_mdm/LOG_MAX_5_8_2024_____18_33_54/log_max_5_8_2024_____18_33_54_alog_csvs/NODE_REPORT_LOCAL.csv', 
                 rel_path = 'missions/ahoi_multi_agent_base/logs/',
                 anchor_labels = {2: 'NED - 2', 6: 'ABE - 6', 9: 'MAX - 9',99: 'NA'}) -> None:
        
          
        # Load the CSV data
        file_path = rel_path+ahoi_csv
        ahoi_df_raw = pd.read_csv(file_path)

        ahoi_df_raw['time'] = pd.to_datetime(ahoi_df_raw['time']) + pd.to_timedelta(4, unit='h')
        ahoi_df_raw['anchor_id'] = ahoi_df_raw['anchor_id'].fillna(99).astype(int)
        ahoi_df_raw['target_id'] = ahoi_df_raw['target_id'].fillna(99).astype(int)

        # Create a dictionary for anchor labels
        # NED - 2, ABE - 6, MAX - 9
        self.anchor_labels = anchor_labels
        self.anchor_colors = {2: 'red', 6: 'green', 9: 'orange'}

        # Map the 'anchor_id' to 'anchor_label'
        ahoi_df_raw['anchor_label'] = ahoi_df_raw['anchor_id'].map(self.anchor_labels)

        self._ahoi_mobile_raw = ahoi_df_raw

        # mobile node
        file_mdm_mobile = rel_path + mobile_csv
        file_mdm_id6 = rel_path + id6_csv
        file_mdm_id9 = rel_path + id9_csv     
        file_mdm_id2 = rel_path + id2_csv
    
        self._df_mdm_mobile = pd.read_csv(file_mdm_mobile, on_bad_lines='skip')
        self._df_mdm_id6 = pd.read_csv(file_mdm_id6, on_bad_lines='skip')
        self._df_mdm_id9 = pd.read_csv(file_mdm_id9, on_bad_lines='skip')
        self._df_mdm_id2 = pd.read_csv(file_mdm_id2, on_bad_lines='skip')

        # Construct datetime objects for the start and end times

        #print(f"Len oak {df_mdm_mobile.size}, len abe {df_mdm_id6.size}, len max {df_mdm_id9.size}, len ned {df_mdm_id2.size}")
        self._df_mdm_mobile['time'] = pd.to_datetime(self._df_mdm_mobile['time'], unit='s')
        self._df_mdm_id6['time'] = pd.to_datetime(self._df_mdm_id6['time'], unit='s')
        self._df_mdm_id9['time'] = pd.to_datetime(self._df_mdm_id9['time'], unit='s')
        self._df_mdm_id2['time'] = pd.to_datetime(self._df_mdm_id2['time'], unit='s')

        self.start_utc = self._ahoi_mobile_raw['time'].iloc[0]
        self.end_utc = self._ahoi_mobile_raw['time'].iloc[-1]

        self.clip_interpolate_data()

    def set_start_end(self, start_utc, end_utc):
        # Manual set new start / End
        # Example
        # start_utc = d_time(2024, 8, 5, 23, 3, 0) 
        # end_utc = d_time(2024, 8, 5, 23, 4, 30)

        self.start_utc = start_utc
        self.end_utc = end_utc

        print(f"Data start at {start_utc} UTC")
        print(f"Data end at {end_utc} UTC")

        self.clip_interpolate_data()

    def df_clip_time(self, input_df, start_utc, end_utc):
        return input_df[(input_df['time'] >= start_utc) & (input_df['time'] <= end_utc)]

    def clip_interpolate_data(self):

        start_time_utc = self.start_utc
        end_time_utc = self.end_utc

        mobile_df = self._df_mdm_mobile
        id2_df = self._df_mdm_id2
        id6_df = self._df_mdm_id6
        id9_df = self._df_mdm_id9


        self.ahoi_df_clipped = self.df_clip_time(self._ahoi_mobile_raw, start_time_utc, end_time_utc)
        
        

        mobile_df_clipped = self.df_clip_time(mobile_df, start_time_utc, end_time_utc)
        id2_df_clipped = self.df_clip_time(id2_df, start_time_utc, end_time_utc)
        id6_df_clipped = self.df_clip_time(id6_df, start_time_utc, end_time_utc)
        id9_df_clipped = self.df_clip_time(id9_df, start_time_utc, end_time_utc)

        #self.ahoi_df_clipped = self._ahoi_mobile_raw[(self._ahoi_mobile_raw['time'] >= start_time_utc) & (self._ahoi_mobile_raw['time'] <= end_time_utc)]
        # mobile_df_clipped =  mobile_df[(mobile_df['time'] >= start_time_utc) & ( mobile_df['time'] <= end_time_utc)]

        # id2_df_clipped = id2_df[(id2_df['time'] >= start_time_utc) & (id2_df['time'] <= end_time_utc)]
        # id6_df_clipped = id6_df[(id6_df['time'] >= start_time_utc) & (id6_df['time'] <= end_time_utc)]
        # id9_df_clipped = id9_df[(id9_df['time'] >= start_time_utc) & (id9_df['time'] <= end_time_utc)]
        


        # Step 1: Create a union of all time points using numpy
        common_time = np.union1d(mobile_df_clipped['time'], id6_df_clipped['time'])
        common_time = np.union1d(common_time, id9_df_clipped['time'])
        common_time = np.union1d(common_time, id2_df_clipped['time'])

        # Step 2: Interpolate data for Oak
        mobile_interp = (
            mobile_df_clipped.set_index('time')
            .reindex(common_time)
            .infer_objects(copy=False)
            .interpolate(method='time')
        )

        # Step 3: Interpolate and calculate distances for each robot

        # Abe - 6
        id6_interpolated = (
            id6_df_clipped.set_index('time')
            .reindex(common_time)
            .infer_objects(copy=False)
            .interpolate(method='time')
        )

        id6_distances = np.sqrt(
            (mobile_interp['X'] - id6_interpolated['X']) ** 2 +
            (mobile_interp['Y'] - id6_interpolated['Y']) ** 2
        ).reset_index(name='id6_dist')

        # Max - 9
        id9_interpolated = (
            id9_df_clipped.set_index('time')
            .reindex(common_time)
            .infer_objects(copy=False)
            .interpolate(method='time')
        )

        id9_distances = np.sqrt(
            (mobile_interp['X'] - id9_interpolated['X']) ** 2 +
            (mobile_interp['Y'] - id9_interpolated['Y']) ** 2
        ).reset_index(name='id9_dist')

        # Ned - 2
        id2_interpolated = (
            id2_df_clipped.set_index('time')
            .reindex(common_time)
            .infer_objects(copy=False)
            .interpolate(method='time')
        )

        id2_distances = np.sqrt(
            (mobile_interp['X'] - id2_interpolated['X']) ** 2 +
            (mobile_interp['Y'] - id2_interpolated['Y']) ** 2
        ).reset_index(name='id2_dist')

        # Step 4: Combine results into a single data frame
        self.distances_combined = id6_distances.merge(id9_distances, on='time').merge(id2_distances, on='time')

    def get_all_anchor_dist_df(self):
        # Return the combined distances
        # 'time', 'id6_dist', 'id9_dist', 'id2_dist'

        return self.distances_combined
    
    def get_mobile_df(self):
        return self._df_mdm_mobile
    
    def get_ahoi_df(self):
        return self.ahoi_df_clipped
    
    def get_anchor_df(self):
        return self._df_mdm_id2, self._df_mdm_id6, self._df_mdm_id9
    
    def get_anchor_labels(self):
        return self.anchor_labels
    
    def get_anchor_colors(self):
        return self.anchor_colors
    
    def get_start_end_utc(self):
        return self.start_utc, self.end_utc
    

class DFReader():
    def __init__(self, df, start_idx=0, end_idx=-1):
        self.df = df
        self.df_start_time = df['time'].iloc[start_idx]
        self.df_end_time = df['time'].iloc[end_idx]
        self.current_index = start_idx
        self.df_length = len(df)

    def get_end_time(self):
        return self.df_end_time
    
    def check_end_of_data(self):
        if self.current_index >= self.df_length-1:
            print(f"End of data reached idx: {self.current_index} df-len:{self.df_length}")
            return True 
    

    def proceed_for_new_data(self, current_time): # roll forward in df to current time

        while self.current_index < self.df_length and current_time >= self.df['time'].iloc[self.current_index]:
            
            self.current_index+=1
            if self.current_index >= self.df_length:
                print("End of data reached")
         
    def get_newest_data(self):
        # Get the current data row
        return self.df.iloc[self.current_index] 
    
    def get_recent_data_at(self,current_time):
        # roll forward in df to current time and return the data row
        self.proceed_for_new_data(current_time)
        return self.get_newest_data()
    
    def to_next_data_row(self, current_time):
        # true if this returns a new data row
        # false if no new data or end of data is reached

        if self.current_index < self.df_length and current_time >= self.df['time'].iloc[self.current_index]: 
            self.current_index+=1
            return True
        else:
            return False
        
class AhoiSimulator():
    def __init__(self, poll_scheme=['tof','tof-pos'], tof_timeout=0.7, pos_timeout=1.3) -> None:
        self.poll_scheme = poll_scheme
        self.scheme_len = len(self.poll_scheme)
        self.poll_scheme_idx = 0

        self.tof_timeout = tof_timeout
        self.pos_timeout = pos_timeout

        self.time_last_poll = None

        self.open_tof_poll = False
        self.open_pos_poll = False

        
    # def set_current_time(self, current_time):
    #     self.current_time = current_time

    def poll_tof(self,current_time):
        self.time_last_poll = current_time
        self.poll_event = 'poll_tof'
        self.open_tof_poll = True

        self.poll_scheme_idx = (self.poll_scheme_idx + 1) % self.scheme_len


        return self.poll_event
    
    def poll_tofpos(self,current_time):
        self.time_last_poll = current_time
        self.poll_event = 'poll_tofpos'
        self.open_tof_poll = True
        self.open_pos_poll = True

        self.poll_scheme_idx = (self.poll_scheme_idx + 1) % self.scheme_len

        return self.poll_event
    
    def reset_poll(self):
        self.open_tof_poll = False
        self.open_pos_poll = False

    def poll_timeout(self, current_time):
        if self.poll_event == 'poll_tof':
            if (current_time - self.time_last_poll).total_seconds() > self.tof_timeout:
                self.reset_poll()
        
        elif self.poll_event == 'poll_tofpos':
            if (current_time - self.time_last_poll).total_seconds() > self.pos_timeout:
                self.reset_poll()
    
    def get_next_anchor(self):
        if self.poll_scheme_idx >= len(self.poll_scheme):
            self.poll_scheme_idx = 0
        return self.poll_scheme[self.poll_scheme_idx]
    
    def ack_tof(self):
        
        self.open_tof_poll = False
        self.ack_event = 'tof_ack'
        return self.ack_event, distance