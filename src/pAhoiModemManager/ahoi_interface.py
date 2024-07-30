#!/usr/bin/env python3

"""
Simple python interface to ahoi-modems


"""
import numpy as np
import json
import time

import ahoi_csv_logger

from collections import deque
from ahoi.modem.modem import Modem

class AhoiInterface():
    def __init__(self, node_config_file, enviro_config_file, anchor_id_list=None, debug_prints=False, logging=False):

        node_config = self.load_config(config_file=node_config_file)
        enviro_config = self.load_config(config_file=enviro_config_file)

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        print(f"\nStarting ahoi interface...")
    
        print("reading config file...")
        connect_device = node_config['dev'] # dev="/dev/ttyAMA0"
        self.my_id = node_config['modem_id']
        print(f"dev={connect_device}")
        print(f"modem_id={self.my_id}")
        print("\n")
        
        self.myModem = Modem()
        self.myModem.connect(connect_device)
        self.myModem.id(id=self.my_id)  # set anchor ID ahoi modem hw -remain on ahoi after reboot - could fail if this message is not received by anchor      

        self.myModem.addRxCallback(self.callback_hw_ranging) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.callback_on_pos_poll) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.callback_on_pos_reply)

        print(f"[Anchor ID {self.my_id}] Ready!")

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.i_am = node_config['node_type']

        self.debug_mode = debug_prints
                
        self.speed_of_sound = enviro_config["speed_of_sound"] # in m/s
        
        self.anchor_list = anchor_id_list # list of all anchor ids - can be None for anchors that are not mobile base

        if self.i_am == "Mobile-Base":
            # Initialize the anchor objects and store them in a dictionary
            try:
                self.remote_anchors = {anchor_id: AnchorModel(anchor_id) for anchor_id in anchor_id_list}
            except:
                print(f"[ahoi_interace] i_am {self.i_am} and need list of remote anchors - only have anchor_id_list = {anchor_id_list}")
                
        elif self.i_am == "Anchor":
            self.my_anchor = AnchorModel(self.my_id)
        
 
        self.myModem.receive(thread=True)

        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.pos_bytelength = 2
        self.transmit_unit = 'cm' # round to [--] for acoustic transmission
        self.reply_wait_time_pos_range = 0.5 # wait time before replying to poll range+pos - range goes first

        self.logging = logging
        if self.logging:
            self.ahoi_logger = ahoi_csv_logger.AhoiCSVLogger("ahoi_interface_log.csv")



    def get_id(self):
        return self.my_id
    
    def who_am_i(self):
        return self.i_am

    
    def trigger_anchor_poll(self, dst_modem_id):

        new_seq = self.remote_anchors[dst_modem_id].get_last_poll_seq()[0] + 1

        self.myModem.send(src=self.my_id,
                            dst=dst_modem_id,       # id of destination modem
                            status=2,               # status 2 trigger HW-range-ACK
                            type=0x7A,              # type for ranging+pos poll [own]
                            payload=bytearray(),    # empty for poll 
                            dsn=new_seq)            # poll_sequence number is max 255 by modem
        
        self.remote_anchors[dst_modem_id].polled_at_seq(new_seq) # note for each anchor that it was polled.

        if self.debug_mode:
            print(f"\n[Base_ID_{self.my_id}] sent range poll to ID {dst_modem_id} sqn {new_seq} ...")
        if self.logging:
            self.ahoi_logger.log_range_poll(base_id=self.my_id, target_id=dst_modem_id, sqn=new_seq)
    
# =====================================================================================
# =====================================================================================
# =====================================================================================

#                        Following required for Anchor Node

# =====================================================================================
# =====================================================================================
# =====================================================================================
    def callback_on_pos_poll(self, pkt):
        # callback replying to position poll [ranging is handled via hw auto reply]
        # 
        # takes own position - replies to poll-sender
        # 
        # mobile-base -- POLL(0x7A) --> THIS Callback@Anchor --> reply Anchor pos (0x7D)
        #
        # =================================================================================

        if pkt.header.type == 0x7A and pkt.header.dst == self.my_id: # if poll for pos is received

            poll_src = pkt.header.src           # read source id
            seq_of_poll = pkt.header.dsn        # read packet sequence number from poll

            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
            my_pos_x, my_pos_y, _, _ = self.my_anchor.get_pos()

            if self.transmit_unit == 'cm':
                my_pos_x_int = int(my_pos_x * 100)  # from [m] --> [cm]
                my_pos_y_int = int(my_pos_y * 100)  # from [m] --> [cm]
            else:
                my_pos_x_int = int(my_pos_x)        # stay in [m]
                my_pos_y_int = int(my_pos_y)        # stay in [m]

            # Ensure they fit into 2 bytes
            if not (-32768 <= my_pos_x_int <= 32767):
                raise ValueError("my_position_x is out of range for 2 bytes.")
            if not (-32768 <= my_pos_y_int <= 32767):
                raise ValueError("my_position_y is out of range for 2 bytes.")

            position = my_pos_x_int.to_bytes(self.pos_bytelength, 'big', signed=True) + my_pos_y_int.to_bytes(self.pos_bytelength, 'big', signed=True)
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
            
            time.sleep(self.reply_wait_time_pos_range)  # wait before sending position, ranging ACK is sent before

            self.myModem.send(src=self.my_id,           # anchor's own id
                              dst=poll_src,             # reply to poll source
                              type=0x7D,                # temp using Ben Hupka's type for position 
                              status=0,                 # no replying with distance
                              payload=position,         # transmit anchor position (type 0x7D)
                              dsn=seq_of_poll)          # seq number of original poll
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

            if self.debug_mode:
                if self.transmit_unit == 'cm':
                    print(f"[Anchor_ID_{self.my_id}] poll {seq_of_poll} by ID_{poll_src} -> my pos {my_pos_x_int}cm, {my_pos_y_int}cm")
                else:
                    print(f"[Anchor_ID_{self.my_id}] poll {seq_of_poll} by ID_{poll_src} -> my pos {my_pos_x_int}, {my_pos_y_int}")
           
# =====================================================================================
# =====================================================================================
# =====================================================================================

#                        Following required for Mobile Base

# =====================================================================================
# =====================================================================================
# =====================================================================================
    def callback_hw_ranging(self, pkt):
        # callback handling modem hw auto reply on polls
        # 
        # updates last known distance to ANCHOR
        # 

        if pkt.header.type == 0x7F and pkt.header.len > 0 and pkt.header.dst == self.my_id:
            anchor_id = pkt.header.src      # anchor_id that sent reply
            seq_of_poll = pkt.header.dsn    # seq of original poll

            # compute TOF
            tof = 0
            for i in range(0, 4):
                tof = tof * 256 + pkt.payload[i]
            distance = tof * 1e-6 * self.speed_of_sound

            self.remote_anchors[anchor_id].update_range(seq=seq_of_poll, new_range=distance) # update range for corresponding anchor

            if self.debug_mode:
                dt_ms = (time.time() - self.remote_anchors[anchor_id].get_last_poll_seq()[1])*1000
                print(f"[Base ID {self.my_id}] TOF-ACK to poll_seq {seq_of_poll} @ {dt_ms:.0f}ms from ANCHOR ID {anchor_id}: distance {distance:.2f}m")

            if self.logging:
                self.ahoi_logger.log_tof_ack(base_id=self.my_id, poll_seq=seq_of_poll, time=dt_ms, 
                                             anchor_id=anchor_id, distance=distance)


    def callback_on_pos_reply(self, pkt):
        # callback receiving Anchor position as result of original on poll
        # 
        # takes own position - replies to poll-sender
        # 
        # mobile-base  --> callback_on_pos_poll@Anchor --> reply pos (0x7D) --> THIS callback
        #
        # ===================================================================================

        if pkt.header.type == 0x7D and pkt.header.len > 0 and pkt.header.dst == self.my_id: # if poll for range+pos is received
            anchor_id = pkt.header.src  # read source id
            seq_of_poll = pkt.header.dsn   # read packet sequence number from poll

            rec_position_x_int = int.from_bytes(pkt.payload[0:self.pos_bytelength], 'big', signed=True) * 1e-2
            rec_position_y_int = int.from_bytes(pkt.payload[self.pos_bytelength:2*self.pos_bytelength], 'big', signed=True) * 1e-2

            if self.transmit_unit == 'cm':
                rec_position_x = rec_position_x_int / 100
                rec_position_y = rec_position_y_int / 100
            else:
                rec_position_x = rec_position_x_int
                rec_position_y = rec_position_y_int

            # update position for corresponding anchor
            self.remote_anchors[anchor_id].update_pos(seq=seq_of_poll, new_pos_x=rec_position_x, new_pos_y=rec_position_y) 

            if self.debug_mode :
                dt_ms = (time.time() - self.remote_anchors[anchor_id].get_last_poll_seq()[1])*1000
                print(f"[Base ID {self.my_id}] POS-ACK to poll_seq {seq_of_poll} @ {dt_ms:.0f}ms from ANCHOR ID {anchor_id}: pos {rec_position_x}m, {rec_position_y}m")
            
            if self.logging:
                self.ahoi_logger.log_pos_ack(base_id=self.my_id, poll_seq=seq_of_poll, time=dt_ms, 
                                             anchor_id=anchor_id, pos_x=rec_position_x, pos_y=rec_position_y)


    def load_config(self,config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config


class AnchorModel():
    def __init__(self, anchor_modem_id):
        
        self.anchor_id = anchor_modem_id
        log_history = 15

        self.start_time = time.time()
        self.start_time_seq = 0

        self.last_polled = 0 # seq when this anchor was last polled

        self.last_range_update = None
        self.last_range_update_time_local = time.time()-self.start_time
        self.range_read = False
        self.anchor_range = None
        self.range_log = deque(maxlen=log_history)
        #  timestamp = datetime.now()
        #  self.signal_log.append((timestamp, signal_received))
        # if len(self.signal_log) == 0:
        #    return 0.0
        # self.anchor_range_update_log = None
        # self.anchor_range_success_rate = 0

        self.last_pos_update = None
        self.last_pos_update_time_local = time.time()-self.start_time
        self.pos_read = False
        self.pos_x = None
        self.pos_y = None
    
    def polled_at_seq(self, seq):
        self.last_polled = seq
        self.start_time_seq = time.time()

    def get_last_poll_seq(self):
        return self.last_polled, self.start_time_seq

    def update_range(self, seq, new_range):    
        self.range_read = False
        self.last_range_update = seq
        self.last_range_update_time_local = time.time()-self.start_time
        self.measured_range = new_range

    def update_pos(self, seq, new_pos_x, new_pos_y):
        self.pos_read = False
        self.last_pos_update = seq
        self.last_pos_update_time_local = time.time()-self.start_time
        self.pos_x = new_pos_x
        self.pos_y = new_pos_y
    
    def get_pos(self, read=False):
        self.pos_read = read
        # output: pos_x [m], pos_y [m], last_range_update [seq], last_range_update_time_local [s]
        return self.pos_x, self.pos_y, self.last_pos_update, self.last_pos_update_time_local

    def get_range(self, read=False):
        self.range_read = read
        # output: dist [m], last_range_update [seq], last_range_update_time_local [s]
        return self.measured_range, self.last_range_update, self.last_range_update_time_local



if __name__ == '__main__':

    modem_id_list = (2,6,9) # list of remote anchor modems
    counter = 0
    try:
        # type (anchor/base) and ID are set via config file
        my_modem = AhoiInterface(node_config_file='local_modem_config.json', 
                                 enviro_config_file='enviro_config.json', 
                                 anchor_id_list=modem_id_list,
                                 debug_prints=True,
                                 logging=True)
        while(True):
            
            
            if my_modem.who_am_i() == "Mobile-Base": # mobile base has id=0
                for poll_id in modem_id_list:

                    my_modem.trigger_anchor_poll(dst_modem_id=poll_id)
                    
                    time.sleep(1.3) # TODO 1. if TOF does not appear - pass, if second arrives - pass
            else:
                #my_modem.my_anchor.update_pos(new_pos_x=10, new_pos_y=42, seq=None)
                time.sleep(1)
            
            if(counter % 15 == 0):
                print(f"\n[ahoi_interface] Counter {counter} - Still alive... ")

            counter+=1


    except KeyboardInterrupt:
        pass
