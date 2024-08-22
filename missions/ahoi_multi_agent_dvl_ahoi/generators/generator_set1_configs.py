#!/bin/python
#Raymond Turrisi

""" 
    This Python file/program, should be considered only a single function to reconstruct specific
    conditions. For example, conditions are hard-coded, and then you pass an index to reconstruct 
    a set of conditions deterministically. Herein, this configuration generator, will always 
    generate a file, which contains initial configuration conditions for five agents. 
    (Agent name, x, y, heading, color), seemingly randomly placed within a polygon. 
"""

#For 1-N agents, generate K random configurations within a region

import sys 
import os 
import numpy as np 
import shapely.geometry as sh

def show_example():
    print("config_set1_generator.py 567")

def show_help():
    pass 

agent_names = ["abe", 
               "ben", 
               "cal", 
               "deb", 
               "eve", 
               "fin", 
               "gus", 
               "hal", 
               "ira", 
               "jen", 
               "ken", 
               "leo", 
               "max", 
               "ned", 
               "oak", 
               "pat", 
               "quin", 
               "rob", 
               "sam", 
               "tim", 
               "uma", 
               "val", 
               "wes", 
               "xan", 
               "yen", 
               "zac"]

agent_colors = [
    "yellow",
    "red",
    "dodger_blue",
    "green",
    "purple",
    "orange",
    "white",
    "dark_green",
    "dark_red",
    "cyan",
    "coral",
    "brown",
    "bisque",
    "white",
    "pink",
    "darkslateblue",
    "brown",
    "burlywood",
    "goldenrod",
    "ivory",
    "khaki",
    "lime",
    "peru",
    "powderblue",
    "plum",
    "sienna",
    "sandybrown",
    "navy",
    "olive",
    "magenta"
]

def get_rnd_point_in_poly(polygon):
    minx, miny, maxx, maxy = polygon.bounds
    point = sh.Point(np.random.uniform(minx,maxx), np.random.uniform(miny, maxy))
    while(not polygon.contains(point)):
        point = sh.Point(np.random.uniform(minx,maxx), np.random.uniform(miny, maxy))
    x,y = point.xy
    return x[0], y[0]

if __name__ == "__main__":
    #Initialize variables
    amt = 0
    cx,cy = 25, -30 #meters from origin warp!
    is_circular = True
    is_polygon = False
    radius = 30 #meters!
    points = []
    n_agents = 5
    #Parse arguments

    if len(sys.argv) == 1:
        print("Improper usage")
        show_example()
        exit(1)

    idx = int(sys.argv[1])

    np.random.seed(idx)

    agent_names = agent_names[0:n_agents]

    if(is_polygon):
        polygon = sh.Polygon(points)
    fname = f"agent_configurations.txt"
    with open(f"{fname}","w") as f:
        f.write(f"# << Generated with \"{sys.argv[0]} {sys.argv[1]}\" >>\n")
        for idx, a in enumerate(agent_names):
            #Get the starting positions      
            if(is_polygon):
                x,y = get_rnd_point_in_poly(polygon)
            else:
                x = cx+np.random.random()*radius
                y = cy+np.random.random()*radius

            #Get the starting heading
            hdg = int(np.random.random()*360)

            #Write the agent and this information to a file
            f.write(f"{a}, {float(x):0.2f}, {float(y):0.2f}, {int(hdg)}, {agent_colors[idx%len(agent_colors)]}")
            if(idx <= len(agent_names)-2):
                f.write("\n")