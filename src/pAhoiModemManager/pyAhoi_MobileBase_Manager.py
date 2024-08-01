#!/usr/bin/env python3

import pymoos
import argparse
import time
import json
from ahoi_interface import AhoiInterface

class pyAhoiMobileBaseManager(object):
    def __init__(self, server_host, server_port, modem_config_file='local_modem_config.json', enviro_config_file='enviro_config.json'):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        ###parameters###
        self.moos_app_name = 'pyAhoi_MobileBase_Manager'
        self.time_warp = 1
        self.server_host = server_host #'localhost'
        self.server_port = server_port #9001 
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

        self.moos_connected = False
        #self.CMD = "" # init. var used for receiving user-posted commands
        
        ''' Initialize Python-MOOS Communications '''
        self.mooscomms = pymoos.comms()
        self.mooscomms.set_on_connect_callback(self.on_connect)
        self.mooscomms.set_on_mail_callback(self.on_new_mail)

        #self.mooscomms.add_active_queue('CMD_queue', self.moos_on_CMD)
        #self.mooscomms.add_message_route_to_active_queue('CMD_queue', 'DVL_CMD')
          
        self.mooscomms.run(self.server_host, self.server_port, self.moos_app_name)
        pymoos.set_moos_timewarp(self.time_warp)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

        # self.node_config = load_config(modem_config_file)
        # self.my_type = self.node_config['type']         # Anchor vs Mobile-Base
        # self.my_vehicle = self.node_config['vehicle']   # AUV (3D) vs ASV (2D)
        # if self.my_vehicle == "AUV":
        #     self.my_dof = 3
        # else:
        #     self.my_dof = 2
        enviro_data = self.load_config(enviro_config_file)
        self.anchor_id_list = enviro_data["anchor_id_list"]

        self.ahoi_interface = AhoiInterface(node_config_file=modem_config_file, enviro_config_file=enviro_config_file,debug_prints=True, logging=True)


        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.my_moos_pos_x = None
        self.my_moos_pos_y = None
        self.my_moos_pos_z = None


    def on_connect(self):
        ''' On connection to MOOSDB, register for desired MOOS variables (allows for * regex) e.g. register('variable', 'community', 'interval')
        self.mooscomms.register('NODE_*_PING','NODE_*',0) '''
        self.moos_connected = True

        print("Connected to MOOSDB")
        self.mooscomms.register('NAV_X', 0)
        self.mooscomms.register('NAV_Y', 0)
        self.mooscomms.register('NAV_Z', 0)
        
        for id in self.anchor_id_list:
            self.mooscomms.register("RANGE_" + str(id), 0)
            self.mooscomms.register("RANGE_" + str(id) + "_SEQ", 0)

            self.mooscomms.register("ANCHOR_" + str(id) + "_POS_X", 0)
            self.mooscomms.register("ANCHOR_" + str(id) + "_POS_Y", 0)
            self.mooscomms.register("ANCHOR_" + str(id) + "_SEQ", 0)

        return True

    def on_new_mail(self):
        for msg in self.mooscomms.fetch():
            if msg.key() == 'NAV_X':
                self.my_moos_pos_x = msg.double()
            elif msg.key() == 'NAV_Y':
                self.my_moos_pos_y = msg.double()
            elif msg.key() == 'NAV_Z':
                self.my_moos_pos_z = msg.double()
        return True
    

    def run(self):
        counter = 0
        rate = 10
        while True:
            if self.moos_connected:
                self.iterate()
                if counter%100 == 0:
                    print(f"[pyAhoi_MobileBase_Manager] still alive ... since {(counter/rate/60):.1f}min")
                time.sleep(1/rate)
                #self.mooscomms.yield_(1)  # Sleep for 1 seconds
                counter+=1

    def iterate(self):
        # TODO 1. notice that range is received
        # TODO 2. notice that pos is received
        # TODO 3. notify accordingly
        for id in self.anchor_id_list:
            self.ahoi_interface.remote_anchors[id]

            if self.ahoi_interface.remote_anchors[id].is_pos_new():
                # check if new anchor position has been received - if so -> notify
                anchor_pos_x, anchor_pos_y, seq, pos_update_time = self.ahoi_interface.remote_anchors[id].get_pos(read=True)

                self.mooscomms.notify("ANCHOR_" + str(id) + "_POS_X", anchor_pos_x ,pymoos.time())
                self.mooscomms.notify("ANCHOR_" + str(id) + "_POS_Y", anchor_pos_y, pymoos.time())
                self.mooscomms.notify("ANCHOR_" + str(id) + "_SEQ", seq, pymoos.time())

            if self.ahoi_interface.remote_anchors[id].is_range_new():
                # check if new range measurement has been received - if so -> notify
                range, seq, range_update_time = self.ahoi_interface.remote_anchors[id].get_range(read=True)
            
                self.mooscomms.notify("RANGE_" + str(id), range, pymoos.time())
                self.mooscomms.notify("RANGE_" + str(id) + "_SEQ", seq ,pymoos.time())




         

        

        #self.ahoi_interface.my_anchor.update_pos(new_pos_x=self.my_moos_pos_x, new_pos_y=self.my_moos_pos_y, seq=None)
        # if self.my_pos_x is not None and self.my_pos_y is not None:
        #     print(f"[AhoiModemManager] set my ASV-MOOS position x={self.my_pos_x:.2f}, y={self.my_pos_y:.2f}")
    
    def load_config(self,config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config

        
        
if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='pyAhoiAnchorManager runner')
    # parser.add_argument('--server_host', required=True, help='Server host address')
    # parser.add_argument('--server_port', type=int, required=True, help='Server port')
    # parser.add_argument('--modem_config_file', default='local_modem_config.json', help='Path to the modem config file')
    # parser.add_argument('--enviro_config_file', default='enviro_config.json', help='Path to the environment config file')
    
    # args = parser.parse_args()

    # # Arguments are passed directly as they are already correctly referenced in the launch.sh
    # app = pyAhoiMobileBaseManager(args.server_host, args.server_port,  args.modem_config_file, args.enviro_config_file)
    app = pyAhoiMobileBaseManager("localhost", 9000,  "local_modem_config.json", "enviro_config.json")
    app.run()