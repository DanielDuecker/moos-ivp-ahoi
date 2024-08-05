import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV data into a DataFrame
df = pd.read_csv('20240801_0118_test.csv')

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter TOF-ACK, POS-ACK, and range_poll events
tof_ack_df = df[df['event'] == 'TOF-ACK']
pos_ack_df = df[df['event'] == 'POS-ACK']
range_poll_df = df[df['event'] == 'range_poll']

# Plotting the distance
plt.figure(figsize=(10, 6))

# Plot TOF-ACK distances
plt.plot(tof_ack_df['timestamp'], tof_ack_df['distance'], 'bo-', label='TOF-ACK Distance')

# Plot POS-ACK distances
plt.plot(pos_ack_df['timestamp'], pos_ack_df['distance'], 'go-', label='POS-ACK Distance')

# Marking TOF and POS received events
plt.scatter(tof_ack_df['timestamp'], tof_ack_df['distance'], color='blue', label='TOF-ACK', marker='o')
plt.scatter(pos_ack_df['timestamp'], pos_ack_df['distance'], color='green', label='POS-ACK', marker='x')

# Marking range_poll events
plt.scatter(range_poll_df['timestamp'], [0] * len(range_poll_df), color='red', label='Range Poll', marker='|')

# Labels and title
plt.xlabel('Timestamp')
plt.ylabel('Distance')
plt.title('Distance Over Time with TOF-ACK, POS-ACK, and Range Poll Events')
plt.legend()
plt.grid(True)

# Show plot
plt.show()
