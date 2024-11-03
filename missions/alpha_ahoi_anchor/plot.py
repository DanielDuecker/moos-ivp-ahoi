#!/bin/python3
# <TEMPLATE>
###### <START>
if __name__ == "__main__":
    import sys
    import os
    import json
    import glob
    import matplotlib.pyplot as plt
    from pyproj import Geod
    import numpy as np
    import pandas as pd
    import warnings
    import cartopy.crs as ccrs
    import cartopy.io.img_tiles as cimgt
    warnings.filterwarnings("ignore")  # Suppress warnings

    # Handle command-line arguments
    sim_mode = "--sim" in sys.argv

    ###### <SETUP>
    # Get the mission directory from command line arguments
    mission_directory = sys.argv[1]

    # Ensure the mission directory path is normalized (removes trailing slashes)
    mission_directory = os.path.normpath(mission_directory)

    # Find the JSON file in the given directory
    glb = glob.glob(os.path.join(mission_directory, "*_mdm", "*whole.json"))
    fname = glb[0]

    # Create the output directory path, ensuring no double slashes
    output_directory = os.path.join(mission_directory, "meta/")

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    # Load the JSON file
    mission_data = json.load(open(fname))
    mission = next(iter(mission_data))

    # Define the variables to extract
    to_plot = {
        'NAV_X': "f",
        'NAV_Y': "f",
    }

    # Helper function to cast data
    def cast(dat, var):
        if var == "f":
            return float(dat)
        elif var == "i":
            return int(dat)
        elif var == "s":
            return str(dat)

    # Extract and process the data
    raw_data = mission_data[mission]['data']
    all_data = []

    # This parsing is only "strange", and is excessive for one vehicle, since
    # the datastructure we are using allows you to extend this to parse data from 
    # shoreside and multiple vehicles at the same time, since for a single mission
    # all get bundled into the same JSON file. Also, the navigation structure for the 
    # json files may seem klunky - but if you drop ROS bags in a directory next to the MOOS_LOG
    # directory, all the data also gets extracted from the ROS bag and can be extracted in this 
    # same loop. 
    # For a single vehicle, one may also just read the CSV files they care about directly. 
    for k, v in to_plot.items():
        if k in raw_data:
            set_data = [[entry[0], cast(entry[1], v)] for entry in raw_data[k]]
            df = pd.DataFrame(set_data, columns=["time", k.lower()]).set_index("time")
            all_data.append(df)

    # Combine all extracted data into one DataFrame
    data_df = pd.concat(all_data, axis=1)
    data_df["t"] = data_df.index
    data_df["t"] = data_df["t"] - data_df["t"].iloc[0]
    data_df.index = data_df["t"]
    ###### Geodesic Conversion
    # Define the WGS84 ellipsoid model
    geod = Geod(ellps="WGS84")

    # Pavlab origin for the geodesic conversion
    LatOrigin = 42.358456
    LongOrigin = -71.087589

    # Convert NAV_X and NAV_Y from Cartesian to Latitude/Longitude. 
    converted_lats = []
    converted_lons = []

    for x, y in zip(data_df['nav_x'], data_df['nav_y']):
        distance = np.sqrt(x**2 + y**2)
        bearing = np.degrees(np.arctan2(x, y))
        lon, lat, _ = geod.fwd(LongOrigin, LatOrigin, bearing, distance)
        converted_lats.append(lat)
        converted_lons.append(lon)

    converted_lats = np.array(converted_lats)
    converted_lons = np.array(converted_lons)

    ###### Plotting Map Overlay
    print("Plotting NAV_X, NAV_Y Track Overlay on Satellite Map")
    fig = plt.figure(figsize=(12, 10))  # Increase width to 12 for a wider figure
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Use OpenStreetMap as the background
    openstreetmap = cimgt.OSM()
    ax.add_image(openstreetmap, 18)  # Adjust zoom level if necessary

    times = data_df.index  # Assuming the DataFrame index represents time

    # Use scatter instead of plot for color mapping
    sc = ax.scatter(converted_lons, converted_lats, s=3, c=times, cmap='cool', marker='o', transform=ccrs.PlateCarree(), label="NAV_X, NAV_Y Track")

    # Add the color bar to the plot
    cbar = plt.colorbar(sc, ax=ax, orientation='vertical', fraction=0.03, pad=0.1)  # Increase the pad for more space
    cbar.set_label('Time')

    ax.set_title('NAV_X, NAV_Y Track Overlay')

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Set extent based on lat/lon values
    lat_range = converted_lats.max() - converted_lats.min()
    lon_range = converted_lons.max() - converted_lons.min()
    max_range = max(lat_range, lon_range)
    padding = max_range * 1.5
    ax.set_extent([converted_lons.min() - padding, converted_lons.max() + padding,
                converted_lats.min() - padding, converted_lats.max() + padding])

    # Add a grid
    ax.gridlines(draw_labels=True)

    # Adjust layout to prevent overlap
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    # Save the figure
    plt.tight_layout()
    plt.savefig(output_directory + 'mission_trajectory.png', dpi=300, bbox_inches='tight')