#!/bin/bash

import numpy as np
import sys 

## Raymond Turrisi

## A basic generator function which given an index between 0 to ub, will repeatedly generate a params file given only an integer

## To replicate this, you would copy this file, rename it, and update the conditions which you would like to vary and the name of the plug files to be generated

## If you already have data which is dependent on a generator function based in a set of parameters, do you under
##  any circumstances change this file, otherwise it defeats the purpose for how this can be used

#####################
#Abstract core generator class which can be used for any collection which is semantically bundled (i.e. the variables and combinations for a specific behavior)
class DeterministicGenerator():
    name = "plug_default_generator_name.moos"
    rules = []
    current_idx = 0
    collections = []

    def __init__(self, _name, _rules, _collections):
        self.name = _name 
        self.rules = _rules
        self.collections = _collections

    def get_to_combination(self, mission_vars, remaining_options, target_idx):
        if len(remaining_options) == 0:
            #Reached base case - now write the arguments to a file
            for r in self.rules:
                if r(mission_vars) == False:
                    return False
            self.current_idx+=1
            if self.current_idx == target_idx:
                with open(self.name, 'w') as f:
                    f.write("// <VARIABLE BLOCK>\n")
                    for k, v in mission_vars.items():
                        f.write(f"\t{k} = {v}\n")
                    f.write("// </VARIABLE BLOCK>")
                    return True
            else:
                return False
        else:
            #for key, vals in remaining_options:
            c = remaining_options.copy()
            key, vals = c.pop()
            for v in vals:
                s = {**mission_vars, key:v}
                if(self.get_to_combination(s, c, target_idx)):
                    return

    #The function which is called by the user to write a collection of plug files to a specific directory, for which only conditions
    # which meet certain rules and conditions will be written. See example. 
    def gen_plug_at_idx(self, target_idx):
        mission_vars = {}
        self.current_idx = 0
        self.get_to_combination(mission_vars, self.collections, target_idx)

    def get_ub_rh(self, mission_vars, remaining_options):
        if len(remaining_options) == 0:
            #Reached base case - now write the arguments to a file
            satisfying = True
            for r in self.rules:
                if r(mission_vars) == False:
                    satisfying = False
            if(satisfying):
                self.current_idx+=1
        else:
            #for key, vals in remaining_options:
            c = remaining_options.copy()
            key, vals = c.pop()
            for v in vals:
                s = {**mission_vars, key:v}
                self.get_ub_rh(s, c)

    #The function which is called by the user to write a collection of plug files to a specific directory, for which only conditions
    # which meet certain rules and conditions will be written. See example. 
    def get_ub(self):
        mission_vars = {}
        self.current_idx = 0
        self.get_ub_rh(mission_vars, self.collections)
        return self.current_idx
#####################


##################### A parameter set which only describes unique collections and rules
class ConvoyVariableSet1(DeterministicGenerator):
    def __init__(self):
        
        name = "plug_bhv_variables.moos"
        compression = list(np.linspace(0,1,3))
        aft_patience = ["true", "false"]
        holding_policy = ["curr_hdg", "setpt_hdg"]
        active_convoying = ["true", "false"]
        full_stop_convoy_range = [1,2]
        slower_convoy_range = list(np.linspace(3,10,3))
        ideal_convoy_range = list(np.linspace(7,20,3))
        faster_convoy_range = list(np.linspace(10,20,3))
        full_lag_convoy_range = list(np.linspace(12,45,3))
        lag_speed_delta = list(np.linspace(0.5,1,3))
        collections = [("compression",compression),
                    ("aft_patience",aft_patience),
                    ("holding_policy",holding_policy),
                    ("active_convoying",active_convoying),
                    ("full_stop_convoy_range",full_stop_convoy_range),
                    ("slower_convoy_range",slower_convoy_range),
                    ("ideal_convoy_range",ideal_convoy_range),
                    ("faster_convoy_range",faster_convoy_range),
                    ("full_lag_convoy_range",full_lag_convoy_range),
                    ("lag_speed_delta",lag_speed_delta)]
        rules = [lambda c: c["full_stop_convoy_range"] < c["slower_convoy_range"],
                 lambda c: c["slower_convoy_range"] < c["ideal_convoy_range"], 
                 lambda c: c["ideal_convoy_range"]< c["faster_convoy_range"],
                 lambda c: c["faster_convoy_range"] < c["full_lag_convoy_range"],
                 ]
        super().__init__(name, rules, collections)
#####################

# Can define multiple generators within this file, and change the behavior to manage a collection of input arguments, rather than just 1

if __name__ == "__main__":

    generator = ConvoyVariableSet1()
    if len(sys.argv) == 1:
        print("Improper usage")
        exit(1)
    if sys.argv[1] == "--ub":
        print(generator.get_ub())
    else:
        idx = int(sys.argv[1])
        generator.gen_plug_at_idx(idx)
    