#!/usr/bin/env python3

"""
Simple python interface to ahoi-modems based on Ben Hupkas code

Feature:
 - trigger range measurement
 - 

"""
import numpy as np
import time
from ahoi.modem.modem import Modem

class AhoiInterface():
    def __init__(self, my_id, base_id, dev="/dev/ttyUSB0"):
        self.myModem = Modem()
        self.myModem.connect(dev)

        self.my_id = my_id      # id of this modem 
        self.base_id = base_id  # id of the (mobile) base modem

        self.dsn = 0 # init packet counter
        

        SPEED_OF_SOUND = 1500 
        self.speed_of_sound = SPEED_OF_SOUND # in m/s

        self.anchor_ids = np.array([1])

        # debug echoing of transmitted and received packages
        # self.myModem.setTxEcho(True)
        # self.myModem.setRxEcho(True)

        self.myModem.addRxCallback(self.rangingCallback) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.rangingPosCallbackPoll) # Add a function to be called on rx pkt
        self.myModem.addRxCallback(self.rangingPosCallbackAck)

        self.myModem.receive(thread=True)

    def trigger_range_poll(self):
        self.dsn += 1 # increase packet sequence
        dst_msg = 255 # 255 = broadcast
        
        self.myModem.send(src=self.base_id,
                            dst=dst_msg,#self.anchor_ids[self.i],
                            status=2,               # status 2 trigger HW-range-ACK
                            type=0x00,              # type for ranging poll - that is auto-replied by the receipent
                            payload=bytearray(),
                            dsn=self.self.dsn)
        
        print(f"[Base with ID {self.my_id}] sent range poll to ID {dst_msg} sqn {self.dsn} ...")
    
    def trigger_pos_range_poll(self, dst_modem_id):
        self.dsn += 1 # increase packet sequence

        self.myModem.send(src=self.base_id,
                            dst=dst_modem_id,       # id of destination modem
                            status=2,
                            type=0x7A,              # type for ranging+pos poll [own]
                            payload=bytearray(),
                            dsn=self.dsn)
        print(f"[Base with ID {self.my_id}] sent range poll to ID {dst_modem_id} sqn {self.dsn} ...")
    


    def rangingPosCallbackPoll(self, pkt):
        if pkt.header.type == 0x7A and pkt.header.dst == self.my_id: # if poll for range+pos is received
            src = pkt.header.src # read source id
            dsn_poll = pkt.header.dsn # read packet sequence number from poll

            time.sleep(1)  # wait before sending position, ranging ACK is sent before
            my_position_x = 42 + int(np.random.rand()*10)
            my_position_y = 84
            position = my_position_x.to_bytes(2, 'big', signed=True) + my_position_y.to_bytes(2, 'big', signed=True)

            self.myModem.send(src=self.my_id,
                              dst=self.base_id,
                              type=0x7D,            # temp using Ben's type for position 
                              status=0, 
                              payload=position)     # transmit anchor position (type 0x7D)
            
            print(f"[Anchor ID {self.my_id}] Received poll seq_num {dsn_poll} from Anchot ID {src} - reply my position: {my_position_x}, {my_position_y}")


    def rangingPosCallbackAck(self, pkt):
        if pkt.header.type == 0x7D and pkt.header.len > 0 and pkt.header.dst == self.my_id: # if poll for range+pos is received
            src = pkt.header.src # read source id
            dsn_poll = pkt.header.dsn # read packet sequence number from poll

            position_x = int.from_bytes(pkt.payload[0:2], 'big', signed=True) * 1e-2
            position_y = int.from_bytes(pkt.payload[2:4], 'big', signed=True) * 1e-2
            
            print(f"[Anchor ID {self.my_id}] Received reply to my poll {dsn_poll} from ANCHOR ID{src}: Received position: {position_x}, {position_y}")






    def rangingCallback(self, pkt):
        # check if we have received a ranging ack
        if pkt.header.type == 0x7F and pkt.header.len > 0:
            src = pkt.header.src
            dsn = pkt.header.dsn

            tof = 0
            for i in range(0, 4):
                tof = tof * 256 + pkt.payload[i]
            distance = tof * 1e-6 * self.speed_of_sound

            print(f"[Anchor ID {self.my_id}] Received auto-TOF from Anchor ID {src} | TODO/Check DSN {dsn}| - measured distance {distance}")

def main():
    
    try:
        my_base  = AhoiInterface(base_id=87,my_id=0,dev="/dev/ttyUSB1")
        while(True):
            #my_base.trigger_range_poll()
            
            #print("still alive...")my_base.trigger_pos_range_poll(dst_modem_id=87)
            time.sleep(1)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()