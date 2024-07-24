#!/usr/bin/env python

# Nucleus DVL Driver - Mark Franklin - 7/20/23
# https://github.com/nortekgroup/nucleus_driver/tree/main/nucleus_driver

#from nucleus_driver import NucleusDriver
import pymoos
import time
#import atexit # used to end measurement etc when program quits

#import pyDVL_config as cfg # config file with dict of user-spec

class pyAhoiModemManager(object):
    def __init__(self):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        ###parameters###
        self.moos_app_name = 'pyAhoiModemManager'
        self.time_warp = 1
        self.server_host = 'localhost'
        self.server_port = 9000 # for oak, since config setting is not setup yet
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

        self.moos_connected = False
        self.CMD = "" # init. var used for receiving user-posted commands
        
        ''' Initialize Python-MOOS Communications '''
        self.mooscomms = pymoos.comms()
        self.mooscomms.set_on_connect_callback(self.moos_on_connect)

        #self.mooscomms.add_active_queue('CMD_queue', self.moos_on_CMD)
        #self.mooscomms.add_message_route_to_active_queue('CMD_queue', 'DVL_CMD')
          
        self.mooscomms.run(self.server_host, self.server_port, self.moos_app_name)
        pymoos.set_moos_timewarp(self.time_warp)

    def moos_on_connect(self):
        ''' On connection to MOOSDB, register for desired MOOS variables (allows for * regex) e.g. register('variable', 'community', 'interval')
        self.mooscomms.register('NODE_*_PING','NODE_*',0) '''
        self.moos_connected = True
        # TODO add ahoi registers
        self.mooscomms.register('DVL_CMD', 0) # user can pass commands to driver
                 
        # begins measurement upon startup
        #self.driver.start_measurement()


        return True

    def run(self):
        while True:
            if self.moos_connected:
                self.iterate()
                time.sleep(0.1)
             

    def iterate(self):
        # Reads and renders (print and Notify) packet
        # If statement bc frequency (script vs. DVL) discrep. -> "Packet= NONE"
        packet = "Moin Ahoi" #self.driver.read_packet()  
        if len(str(packet)) >= 2:
            self.mooscomms.notify("AHOI_ITERATE_TEST", str(packet), pymoos.time())
            print(packet)
            print("\n")


    # def moos_on_CMD(self, msg):
    #     self.CMD = msg.string() # string?
    #     #  Allows user to query continuous command with "~" -> starts after response
    #     if self.CMD[0] == "~":
    #         self.CMD = self.CMD[1:]
    #         return self.raise_command(True)
    #     return self.raise_command(False)
        
if __name__ == '__main__':
    app = pyAhoiModemManager()
    app.run()
    
