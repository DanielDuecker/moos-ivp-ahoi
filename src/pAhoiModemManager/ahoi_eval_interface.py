import pandas as pd

# Load the CSV file into a pandas DataFrame
csv_file = 'ahoi_interface_log.csv'
data = pd.read_csv(csv_file)

# Function to evaluate the CSV file for each anchor node
def evaluate_csv_per_anchor(data):
    # Group the data by anchor_id
    anchor_groups = data.groupby('anchor_id')

    # Evaluate each anchor group separately
    for anchor_id, group in anchor_groups:
        print(f"Evaluating data for Anchor ID {anchor_id}:")
        
        # Count the number of each event type
        event_counts = group['event'].value_counts()
        print("Event Counts:")
        print(event_counts)
        print()
        
        # Calculate the average distance from TOF-ACK events
        tof_ack_data = group[group['event'] == 'TOF-ACK']
        if not tof_ack_data.empty:
            average_distance = tof_ack_data['distance'].mean()
            print(f"Average Distance from TOF-ACK events: {average_distance:.2f}m")
        else:
            print("No TOF-ACK events to calculate average distance.")
        print()
        
        # Calculate the average positions (pos_x, pos_y) from POS-ACK events
        pos_ack_data = group[group['event'] == 'POS-ACK']
        if not pos_ack_data.empty:
            average_pos_x = pos_ack_data['pos_x'].mean()
            average_pos_y = pos_ack_data['pos_y'].mean()
            print(f"Average Position from POS-ACK events: ({average_pos_x:.2f}m, {average_pos_y:.2f}m)")
        else:
            print("No POS-ACK events to calculate average positions.")
        print()
        
# Evaluate the CSV file for each anchor node
evaluate_csv_per_anchor(data)
