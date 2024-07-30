import csv
from datetime import datetime

class AhoiCSVLogger():
    def __init__(self, log_file = "ahoi_interface_log.csv"):
        self.csv_file = log_file
    # Initialize the CSV file with headers
    #def initialize_csv():
        with open(self.csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write headers
            writer.writerow([
                'timestamp', 'base_id', 'target_id', 'sequence_number', 
                'event', 'time', 'anchor_id', 'distance', 'pos_x', 'pos_y'
            ])

    # Function to log range poll events
    def log_range_poll(self,base_id, target_id, sqn):
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now(), base_id, target_id, sqn, 
                'range_poll', None, None, None, None, None
            ])

    # Function to log TOF-ACK events
    def log_tof_ack(self, base_id, poll_seq, time, anchor_id, distance):
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now(), base_id, None, poll_seq, 
                'TOF-ACK', time, anchor_id, distance, None, None
            ])

    # Function to log POS-ACK events
    def log_pos_ack(self, base_id, poll_seq, time, anchor_id, pos_x, pos_y):
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now(), base_id, None, poll_seq, 
                'POS-ACK', time, anchor_id, None, pos_x, pos_y
            ])