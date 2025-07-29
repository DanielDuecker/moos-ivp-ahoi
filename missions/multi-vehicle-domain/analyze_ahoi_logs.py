#!/usr/bin/env python3

import csv
import sys
from collections import defaultdict
import statistics

def analyze_ahoi_csv(filename):
    # Initialize counters and data storage
    anchors = [2, 6, 9]
    data = {
        anchor: {
            'pings': 0,
            'ranges': 0,
            'positions': 0,
            'range_values': [],
            'pos_x': [],
            'pos_y': []
        } for anchor in anchors
    }
    
    # Read and analyze the CSV file
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            event = row['event']
            
            # For TOF-POS-poll, use target_id
            if event == 'TOF-POS-poll':
                target_id = row.get('target_id', '').strip()
                if target_id and target_id.isdigit():
                    target_id = int(target_id)
                    if target_id in anchors:
                        data[target_id]['pings'] += 1
            
            # For TOF-ACK and POS-ACK, use anchor_id
            else:
                anchor_id = row.get('anchor_id', '').strip()
                if anchor_id and anchor_id.isdigit():
                    anchor_id = int(anchor_id)
                    if anchor_id in anchors:
                        # Count ranges (TOF-ACK)
                        if event == 'TOF-ACK':
                            data[anchor_id]['ranges'] += 1
                            if row['distance']:
                                try:
                                    distance = float(row['distance'])
                                    data[anchor_id]['range_values'].append(distance)
                                except ValueError:
                                    pass
                        
                        # Count positions (POS-ACK)
                        elif event == 'POS-ACK':
                            data[anchor_id]['positions'] += 1
                            if row['pos_x'] and row['pos_y']:
                                try:
                                    x = float(row['pos_x'])
                                    y = float(row['pos_y'])
                                    data[anchor_id]['pos_x'].append(x)
                                    data[anchor_id]['pos_y'].append(y)
                                except ValueError:
                                    pass
    
    # Print results
    print(f"\nAnalysis of: {filename}")
    print("=" * 80)
    
    for anchor in anchors:
        print(f"\nAnchor {anchor}:")
        print(f"  Pings (TOF-POS-poll): {data[anchor]['pings']}")
        print(f"  Ranges (TOF-ACK): {data[anchor]['ranges']}")
        print(f"  Position updates (POS-ACK): {data[anchor]['positions']}")
        
        # Range statistics
        if data[anchor]['range_values']:
            ranges = data[anchor]['range_values']
            print(f"\n  Range statistics:")
            print(f"    Min: {min(ranges):.2f} m")
            print(f"    Max: {max(ranges):.2f} m")
            print(f"    Mean: {statistics.mean(ranges):.2f} m")
        
        # Position statistics
        if data[anchor]['pos_x'] and data[anchor]['pos_y']:
            x_vals = data[anchor]['pos_x']
            y_vals = data[anchor]['pos_y']
            print(f"\n  Position statistics:")
            print(f"    X range: [{min(x_vals):.2f}, {max(x_vals):.2f}] m")
            print(f"    Y range: [{min(y_vals):.2f}, {max(y_vals):.2f}] m")
            print(f"    Mean position: ({statistics.mean(x_vals):.2f}, {statistics.mean(y_vals):.2f}) m")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_ahoi_logs.py <csv_file>")
        sys.exit(1)
    
    try:
        analyze_ahoi_csv(sys.argv[1])
    except FileNotFoundError:
        print(f"Error: File '{sys.argv[1]}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing file: {e}")
        sys.exit(1)