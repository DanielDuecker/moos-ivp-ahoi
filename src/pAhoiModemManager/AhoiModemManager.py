#!/usr/bin/env python3

import pymoos
import time
import json
from ahoi_interface import AhoiInterface, load_config

class AhoiModemManager:
    def __init__(self, moos_server, moos_port, moos_name, config_file='modem_config.json'):
        self.comms = pymoos.comms()
        self.comms.set_on_connect_callback(self.on_connect)
        self.comms.set_on_mail_callback(self.on_new_mail)
        
        self.config = load_config(config_file)
        self.ahoi_interface = AhoiInterface(self.config)
        
        self.comms.run(moos_server, moos_port, moos_name)
        
    def on_connect(self):
        print("Connected to MOOSDB")
        self.comms.register('TRIGGER_RANGE', 0)
        self.comms.register('TRIGGER_POS_RANGE', 0)
        return True

    def on_new_mail(self):
        for msg in self.comms.fetch():
            if msg.key() == 'TRIGGER_RANGE':
                self.ahoi_interface.trigger_range_poll()
            elif msg.key() == 'TRIGGER_POS_RANGE':
                dst_modem_id = int(msg.string())
                self.ahoi_interface.trigger_pos_range_poll(dst_modem_id)
        return True

    def run(self):
        while True:
            self.comms.yield_(1)  # Sleep for 1 second
            time.sleep(0.1)  # Small delay to avoid CPU hogging

if __name__ == "__main__":
    moos_server = 'localhost'
    moos_port = 9000
    moos_name = 'pymoos_ahoi_interface'
    config_file = 'modem_config.json'
    
    app = AhoiModemManager(moos_server, moos_port, moos_name, config_file)
    app.run()
