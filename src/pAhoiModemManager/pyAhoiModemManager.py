#!/usr/bin/env python3

import pymoos
import time
from ahoi_interface import AhoiInterface, load_config

class pyAhoiModemManager(object):
    def __init__(self, config_file='modem_config.json'):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        ###parameters###
        self.moos_app_name = 'pyAhoiModemManager'
        self.time_warp = 1
        self.server_host = 'localhost'
        self.server_port = 9000 # for oak, since config setting is not setup yet
        
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

        self.config = load_config(config_file)
        self.ahoi_interface = AhoiInterface(self.config)


        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.my_pos_x = None
        self.my_pos_y = None




    def on_connect(self):
        ''' On connection to MOOSDB, register for desired MOOS variables (allows for * regex) e.g. register('variable', 'community', 'interval')
        self.mooscomms.register('NODE_*_PING','NODE_*',0) '''
        self.moos_connected = True

        print("Connected to MOOSDB")
        #self.mooscomms.register('TRIGGER_RANGE', 0)
        #self.mooscomms.register('TRIGGER_POS_RANGE', 0)
        self.mooscomms.register('NAV_X', 0)
        self.mooscomms.register('NAV_Y', 0)
        return True

    def on_new_mail(self):
        for msg in self.mooscomms.fetch():
            if msg.key() == 'NAV_X':
                self.my_pos_x = msg.double()
            elif msg.key() == 'NAV_Y':
                self.my_pos_y = msg.double()
                #dst_modem_id = int(msg.string())
                #self.ahoi_interface.trigger_pos_range_poll(dst_modem_id)
        return True
    

    def run(self):
        while True:
            if self.moos_connected:
                self.iterate()
                #self.comms.yield_(1)  # Sleep for 1 second
                dst_modem_id = 42
                self.ahoi_interface.trigger_pos_range_poll(dst_modem_id)
                #self.ahoi_interface.trigger_range_poll()
                time.sleep(1.5)
             

    def iterate(self):
        # Reads and renders (print and Notify) packet
        packet = "Moin Ahoi" 
        if len(str(packet)) >= 2:
            self.mooscomms.notify("AHOI_ITERATE_TEST", str(packet), pymoos.time())
            print(packet)
            print("\n")


        
if __name__ == '__main__':
    app = pyAhoiModemManager()
    app.run()
    
