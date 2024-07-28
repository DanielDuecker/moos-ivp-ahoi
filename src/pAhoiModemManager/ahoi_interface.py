#!/usr/bin/env python3

"""
Simple python interface to ahoi-modems

Feature:
 - trigger range measurement
 - 

"""
import numpy as np
import json
import time
from ahoi.modem.modem import Modem

class AhoiInterface():
    def __init__(self, node_config, enviro_config,  debug_prints=True):
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
        self.myModem.id(id=self.my_id)      

        self.myModem.addRxCallback(self.rangingCallback) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.rangingPosCallbackPoll) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.rangingPosCallbackAck)

        print(f"[Anchor ID {self.my_id}] Ready!")

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.debug_mode = debug_prints
        

        self.dsn = 0 # init packet counter
        
        self.speed_of_sound = enviro_config["speed_of_sound"] # in m/s
        

 
        self.myModem.receive(thread=True)

        self._success_rate_tof_counter = 0
        self._success_rate_pos_counter = 0
        
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        self.pos_bytelength = 2
        self.transmit_unit = 'cm' # round to [--] for acoustic transmission

        self.my_position_x = 0 
        self.my_position_y = 0 
        self.my_position_z = 0 
    
    def get_id(self):
        return self.my_id

    def trigger_range_poll(self):
        self.dsn += 1 # increase packet sequence
        dst_msg = 255 # 255 = broadcast
        
        self.myModem.send(src=self.my_id,
                            dst=dst_msg,#self.anchor_ids[self.i],
                            status=2,               # status 2 trigger HW-range-ACK
                            type=0x00,              # type for ranging poll - that is auto-replied by the receipent
                            payload=bytearray(),
                            dsn=self.self.dsn)
        if self.debug_mode:
            print(f"\n[Base_ID_{self.my_id}] sent range poll to ID {dst_msg} sqn {self.dsn} ...") # TODO dsn max 255
    
    def trigger_pos_range_poll(self, dst_modem_id):
        self.dsn += 1 # increase packet sequence

        self.myModem.send(src=self.my_id,
                            dst=dst_modem_id,       # id of destination modem
                            status=2,
                            type=0x7A,              # type for ranging+pos poll [own]
                            payload=bytearray(),
                            dsn=self.dsn)
        if self.debug_mode:
            print(f"\n[Base_ID_{self.my_id}] sent range poll to ID {dst_modem_id} sqn {self.dsn} ...") # TODO dsn max 255
    


    def rangingPosCallbackPoll(self, pkt):
        if pkt.header.type == 0x7A and pkt.header.dst == self.my_id: # if poll for range+pos is received
            poll_src = pkt.header.src # read source id
            dsn_poll = pkt.header.dsn # read packet sequence number from poll

            time.sleep(0.5)  # wait before sending position, ranging ACK is sent before
            
            if self.transmit_unit == 'cm':
                my_position_x_int = int(self.my_position_x * 100)
                my_position_y_int = int(self.my_position_y * 100)
            else:
                my_position_x_int = int(self.my_position_x)
                my_position_y_int = int(self.my_position_y)

            # Ensure they fit into 2 bytes
            if not (-32768 <= my_position_x_int <= 32767):
                raise ValueError("my_position_x is out of range for 2 bytes.")
            if not (-32768 <= my_position_y_int <= 32767):
                raise ValueError("my_position_y is out of range for 2 bytes.")

            position = my_position_x_int.to_bytes(self.pos_bytelength, 'big', signed=True) + my_position_y_int.to_bytes(self.pos_bytelength, 'big', signed=True)

            self.myModem.send(src=self.my_id,
                              dst=poll_src,
                              type=0x7D,            # temp using Ben's type for position 
                              status=0, 
                              payload=position, # transmit anchor position (type 0x7D)
                              dsn=dsn_poll)     
            if self.debug_mode:
                print(f"[Anchor_ID_{self.my_id}] poll {dsn_poll} by ID_{poll_src} -> my pos {self.my_position_x}, {self.my_position_y}")


    def rangingPosCallbackAck(self, pkt):
        if pkt.header.type == 0x7D and pkt.header.len > 0 and pkt.header.dst == self.my_id: # if poll for range+pos is received
            ack_src = pkt.header.src # read source id
            dsn_poll = pkt.header.dsn # read packet sequence number from poll

            rec_position_x_int = int.from_bytes(pkt.payload[0:self.pos_bytelength], 'big', signed=True) * 1e-2
            rec_position_y_int = int.from_bytes(pkt.payload[self.pos_bytelength:2*self.pos_bytelength], 'big', signed=True) * 1e-2

            if self.transmit_unit == 'cm':
                rec_position_x = rec_position_x_int / 100
                rec_position_y = rec_position_y_int / 100
            else:
                rec_position_x = rec_position_x_int
                rec_position_y = rec_position_y_int

            self._success_rate_pos_counter +=1
            success_rate_pos = self._success_rate_pos_counter / dsn_poll
            
            if self.debug_mode:
                print(f"[Anchor_ID_{self.my_id}, pos_rate {success_rate_pos:.2f}] POS-ACK to my poll {dsn_poll} from ANCHOR ID {ack_src}: Rec pos {rec_position_x}, {rec_position_y}")


    def sim_own_position(self, x_m=42, y_m=84, noisy=True):
        
        self.my_position_x = x_m
        self.my_position_y = y_m
        if noisy:
            self.my_position_x += int(np.random.rand()*10)
        

        return True

    def set_own_position(self, x_m, y_m):
        # to be used by eg. Heron to set own position known from GPS
        if x_m != None and y_m != None:
            self.my_position_x = x_m
            self.my_position_y = y_m
            return True
        else:
            return False





    def rangingCallback(self, pkt):
        # baseline ranging using the modem's HW auto ranging ACK
        # check if we have received a ranging ack
        #
        # Filters for own send ranging-polls
        if pkt.header.type == 0x7F and pkt.header.len > 0 and pkt.header.dst == self.my_id:
            #print(f"dst = {pkt.header.dst}")
            ack_src = pkt.header.src
            dsn = pkt.header.dsn

            tof = 0
            for i in range(0, 4):
                tof = tof * 256 + pkt.payload[i]
            distance = tof * 1e-6 * self.speed_of_sound

            self._success_rate_tof_counter +=1
            success_rate_tof = self._success_rate_tof_counter / dsn

            if self.debug_mode:
                print(f"[Anchor ID {self.my_id}, tof_rate {success_rate_tof:.2f}] TOF-ACK to with dsn {dsn} from ANCHOR ID {ack_src}: - measured distance {distance:.2f}")


def load_config(config_file='local_modem_config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config


if __name__ == '__main__':
    node_config = load_config(config_file='local_modem_config.json')
    enviro_config = load_config(config_file='enviro_config.json')
    modem_id_list = (6,2)
    counter = 0
    try:
        my_modem = AhoiInterface(node_config, enviro_config)
        while(True):
            
            
            if my_modem.get_id() == 0: # mobile base has id=0
                for poll_id in modem_id_list:
                    my_modem.trigger_pos_range_poll(dst_modem_id=poll_id)
                    time.sleep(1.5)
            else:
                my_modem.sim_own_position(noisy=True)
                time.sleep(1)
            
            if(counter % 10 == 0):
                print(f"\n[Counter {counter}] Still alive... ")

            counter+=1


    except KeyboardInterrupt:
        pass
