#!/usr/bin/env python3

#####################################################################
# Copyright 2023 Aurora Flight Sciences. All rights reserved.       #
# This work, authored by Aurora Flight Sciences, was funded         #
# in whole or in part by the U.S. Government under DARPA            #
# Contract No. Agreement N6523623C8011. Use, duplication, or        #
# disclosure is subject to the restrictions as stated in            #
# Agreement N6523623C8011 between the Government and the            #
# Performer. All other rights are reserved by the copyright owner.  #
#####################################################################

##############################################
# add this to the respective .moos file
#      - path from .moos file to pymoos_app
#     Run = ../../src/pAhoiModemManager/pymoos_app_base_template.py  @ NewConsole = true, ExtraProcessParams=PythonParams
#     PythonParams = ServerHost,$(MOOS_PORT),$(VNAME)



import sys
import time
import pymoos

class pymoosAhoiTest(object):
    def __init__(self, server_host, server_port):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        ###parameters###
        self.moos_app_name = 'pymoosAhoiTest'
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

        self.mooscomms.run(self.server_host, self.server_port, self.moos_app_name)
        pymoos.set_moos_timewarp(self.time_warp)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.my_moos_pos_x = None
        self.my_moos_pos_y = None
        self.my_moos_pos_z = None

    def run(self):
        while True:
            print("py moos test alive")
            time.sleep(0.5)

    def on_connect(self):
        ''' On connection to MOOSDB, register for desired MOOS variables (allows for * regex) e.g. register('variable', 'community', 'interval')
        self.mooscomms.register('NODE_*_PING','NODE_*',0) '''
        self.moos_connected = True

        print("Connected to MOOSDB")
        self.mooscomms.register('NAV_X', 0)
        self.mooscomms.register('NAV_Y', 0)
        self.mooscomms.register('NAV_Z', 0)
        
    
    def on_new_mail(self):
        for msg in self.mooscomms.fetch():
            if msg.key() == 'NAV_X':
                self.my_moos_pos_x = msg.double()
                print("new message:", msg.key(), ":", msg.double())
            elif msg.key() == 'NAV_Y':
                self.my_moos_pos_y = msg.double()
            elif msg.key() == 'NAV_Z':
                self.my_moos_pos_z = msg.double()
        return True


if __name__ == '__main__':
    print(f"[pymoosAhoiTest] main starting ...")
    time.sleep(1)
    hostname = sys.argv[3]
    hostport = int(sys.argv[4])

    app = pymoosAhoiTest(server_host=hostname, server_port=hostport)
    app.run()