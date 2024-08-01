import csv
import os
from datetime import datetime

class AhoiCSVLogger():
    def __init__(self, log_file_prefix="ahoi_interface_log"):
        # Determine the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create a timestamp string for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combine the directory, prefix, timestamp, and extension to create the full file path
        self.csv_file = os.path.join(script_dir, f"{log_file_prefix}_{timestamp}.csv")
        
        # Initialize the CSV file with headers
        with open(self.csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write headers
            writer.writerow([
                'timestamp', 'base_id', 'target_id', 'sequence_number', 
                'event', 'time', 'anchor_id', 'distance', 'pos_x', 'pos_y'
            ])

    # Function to log range poll events
    def log_range_poll(self, base_id, target_id, sqn):
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


if __name__ == '__main__':
    # Example usage
    logger = AhoiCSVLogger(log_file_prefix="test_ahoi_interface_log")
    logger.log_range_poll(3, 6, 1)
    logger.log_tof_ack(3, 1, 680.1848411560059, 6, 26.1615)
    logger.log_pos_ack(3, 1, 1156.2013626098633, 6, 0.3511, -0.0702)