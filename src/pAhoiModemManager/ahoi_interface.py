#!/usr/bin/env python3

"""
Simple python interface to ahoi-modems


"""
import numpy as np
import json
import time
from collections import deque
from ahoi.modem.modem import Modem

class AhoiInterface():
    def __init__(self, node_config_file, enviro_config_file, anchor_id_list=None, debug_prints=False):

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
        i_am = node_config['node_type']
        self.debug_mode = debug_prints
                
        self.speed_of_sound = enviro_config["speed_of_sound"] # in m/s
        
        self.anchor_list = anchor_id_list # list of all anchor ids - can be None for anchors that are not mobile base

        if i_am == "Mobile-Base":
            # Initialize the anchor objects and store them in a dictionary
            try:
                self.remote_anchors = {anchor_id: AnchorModel(anchor_id) for anchor_id in anchor_id_list}
            except:
                print(f"[ahoi_interace] i_am {i_am} and need list of remote anchors - only have anchor_id_list = {anchor_id_list}")
                
        elif i_am == "Anchor":
            self.my_anchor = AnchorModel(self.my_id)
        
 
        self.myModem.receive(thread=True)

        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.pos_bytelength = 2
        self.transmit_unit = 'cm' # round to [--] for acoustic transmission
        self.reply_wait_time_pos_range = 0.5 # wait time before replying to poll range+pos - range goes first

    
    def get_id(self):
        return self.my_id

    
    def trigger_anchor_poll(self, dst_modem_id):

        new_seq = self.remote_anchors[dst_modem_id].get_last_poll_seq() + 1

        self.myModem.send(src=self.my_id,
                            dst=dst_modem_id,       # id of destination modem
                            status=2,               # status 2 trigger HW-range-ACK
                            type=0x7A,              # type for ranging+pos poll [own]
                            payload=bytearray(),    # empty for poll 
                            dsn=new_seq)            # poll_sequence number is max 255 by modem
        
        self.remote_anchors[dst_modem_id].polled_at_seq(new_seq) # note for each anchor that it was polled.

        if self.debug_mode:
            print(f"\n[Base_ID_{self.my_id}] sent range poll to ID {dst_modem_id} sqn {new_seq} ...")
    
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
            my_pos_x, my_pos_y, _ = self.my_anchor.get_pos()

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
                print(f"[Base ID {self.my_id}] TOF-ACK to poll_seq {seq_of_poll} from ANCHOR ID {anchor_id}: distance {distance:.2f}m")



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
                print(f"[Base ID {self.my_id}] POS-ACK to poll_seq {seq_of_poll} from ANCHOR ID {anchor_id}: pos {rec_position_x}m, {rec_position_y}m")


    def load_config(self,config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
        return config


class AnchorModel():
    def __init__(self, anchor_modem_id):
        
        self.anchor_id = anchor_modem_id
        log_history = 15

        self.last_polled = 0 # seq when this anchor was last polled

        self.last_range_update = None
        self.anchor_range = None
        self.range_log = deque(maxlen=log_history)
        #  timestamp = datetime.now()
        #  self.signal_log.append((timestamp, signal_received))
        # if len(self.signal_log) == 0:
        #    return 0.0
        # self.anchor_range_update_log = None
        # self.anchor_range_success_rate = 0

        self.last_pos_update = None
        self.pos_x = None
        self.pos_y = None
    
    def polled_at_seq(self, seq):
        self.last_polled = seq

    def get_last_poll_seq(self):
        return self.last_polled

    def update_range(self, seq, new_range):    
        self.last_range_update = seq
        self.measured_range = new_range

    def update_pos(self, seq, new_pos_x, new_pos_y):
        self.last_pos_update = seq
        self.pos_x = new_pos_x
        self.pos_y = new_pos_y
    
    def get_pos(self):
        return self.pos_x, self.pos_y, self.last_pos_update

    def get_range(self):
        return self.measured_range, self.last_range_update

        

if __name__ == '__main__':

    modem_id_list = (2,6,9)
    counter = 0
    try:
        # type (anchor/base) and ID are set via config file
        my_modem = AhoiInterface(node_config_file='local_modem_config.json', enviro_config_file='enviro_config.json', anchor_id_list=(2,6,9),debug_prints=True)
        while(True):
            
            
            if my_modem.get_id() == 0: # mobile base has id=0
                for poll_id in modem_id_list:

                    my_modem.trigger_anchor_poll(dst_modem_id=poll_id)
                    
                    time.sleep(1.5)
            else:
                my_modem.my_anchor.update_pos(new_pos_x=10, new_pos_y=42, seq=None)
                time.sleep(1)
            
            if(counter % 10 == 0):
                print(f"\n[ahoi_interface] Counter {counter} - Still alive... ")

            counter+=1


    except KeyboardInterrupt:
        pass
