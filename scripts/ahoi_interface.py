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
    def __init__(self, base_id, my_id):
        self.myModem = Modem()
        self.myModem.connect("/dev/ttyUSB0")

        self.base_id = base_id  # id of the (mobile) base modem
        self.my_id = my_id      # id of this modem 

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
        self.myModem.send(src=self.base_id,
                            dst=255,#self.anchor_ids[self.i],
                            status=2,               # status 2 trigger HW-range-ACK
                            type=0x00,              # type for ranging poll - that is auto-replied by the receipent
                            payload=bytearray())
        print("sent range poll ...")
    
    def trigger_pos_range_poll(self, dst_modem_id):
        self.myModem.send(src=self.base_id,
                            dst=dst_modem_id,       # id of destination modem
                            status=2,
                            type=0x7A,              # type for ranging+pos poll [own]
                            payload=bytearray())
        print("sent range-pos poll ...")
    


    def rangingPosCallbackPoll(self, pkt):
        if pkt.header.type == 0x7A and pkt.header.len > 0 and pkt.header.dst == self.my_id: # if poll for range+pos is received
            src = pkt.header.src

            #time.sleep(0.5)  # wait before sending position, ranging ACK is sent before
            my_position_x = 42
            my_position_y = 84
            position = my_position_x.to_bytes(2, 'big', signed=True) + my_position_y.to_bytes(2, 'big', signed=True)

            self.myModem.send(src=self.my_id,
                              dst=self.base_id,
                              type=0x7D,            # temp using Ben's type for position 
                              status=0, 
                              payload=position)     # transmit anchor position (type 0x7D)
            
            print(f"\n[ANCHOR] Sent position: {my_position_x}, {my_position_y}\n")


    def rangingPosCallbackAck(self, pkt):
        if pkt.header.type == 0x7D and pkt.header.len > 0 and pkt.header.dst == self.my_id: # if poll for range+pos is received
            src = pkt.header.src

            #position = my_position_x.to_bytes(2, 'big', signed=True) + my_position_y.to_bytes(2, 'big', signed=True)
            
            position_y = int.from_bytes(pkt.payload[0:2], 'big', signed=True) * 1e-2
            position_x = int.from_bytes(pkt.payload[2:4], 'big', signed=True) * 1e-2

            
            
            print(f"\n[ANCHOR] Received position: {position_x}, {position_y}\n")






    def rangingCallback(self, pkt):
        # check if we have received a ranging ack
        if pkt.header.type == 0x7F and pkt.header.len > 0:
            src = pkt.header.src
            # if src == self.anchor_ids[
            #         0]:  # map anchor ids auf 0,1,2 Logik von estimator
            #     id = 0
            # elif src == self.anchor_ids[1]:
            #     id = 1
            # elif src == self.anchor_ids[2]:
            #     id = 2
            # dst = pkt.header.dst
            # type = pkt.header.type
            # status = pkt.header.status
            #self.publish_received_packets(id, dst, type, status)

            tof = 0
            for i in range(0, 4):
                tof = tof * 256 + pkt.payload[i]
            distance = tof * 1e-6 * self.speed_of_sound
            # self.get_logger().info(f"distance to {src}: %6.2f" % (distance))


            print("measured distance to "+ str(src) + ": " + str(distance))
            #self.publish_distance(id, distance)

        # check if we have received position update
        if pkt.header.type == 0x7D and pkt.header.len > 0:
            src = pkt.header.src
            # if src == self.anchor_ids[0]:
            #     id = 0
            # elif src == self.anchor_ids[1]:
            #     id = 1
            # elif src == self.anchor_ids[2]:
            #     id = 2
            dst = pkt.header.dst
            type = pkt.header.type
            status = pkt.header.status
            self.publish_received_packets(id, dst, type, status)

            position_y = int.from_bytes(
                pkt.payload[0:2],
                'big',  # position north
                signed=True) * 1e-2
            position_x = int.from_bytes(
                pkt.payload[2:4],
                'big',  # position east
                signed=True) * 1e-2
            # self.get_logger().info(
            #     f"position of anchor {src}: x = {position_x}, y = {position_y}")

            self.publish_anchor_pose(id, position_x, position_y)

        # # check if we have received initial position
        # if pkt.header.type == 0x7B and pkt.header.len > 0:
        #     src = pkt.header.src
        #     if src == self.anchor_ids[0]:
        #         id = 0
        #     elif src == self.anchor_ids[1]:
        #         id = 1
        #     elif src == self.anchor_ids[2]:
        #         id = 2
        #     dst = pkt.header.dst
        #     type = pkt.header.type
        #     status = pkt.header.status
        #     self.publish_received_packets(id, dst, type, status)

        #     position_y = int.from_bytes(pkt.payload[0:2], 'big',
        #                                 signed=True) * 1e-2
        #     position_x = int.from_bytes(pkt.payload[2:4], 'big',
        #                                 signed=True) * 1e-2
        #     # self.get_logger().info(
        #     #     f"initial position of anchor {src}: x = {position_x}, y = {position_y}"
        #     # )
        #     self.initial_position_bool[id] = True

        #     self.publish_anchor_pose(id, position_x, position_y)

def main():
    
    try:
        my_base  = AhoiInterface(base_id=1,my_id=0)
        while(True):
            my_base.trigger_range_poll()
            time.sleep(1)

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
