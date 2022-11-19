#!/usr/bin/env python3
import sys
import time
import serial
import threading
import queue
from bow_crc import crc, add_crc
from packagePrinter import printPacket
from message_parser import MessageParser


class Message:
  def __init__(self, source, target, type, size, message):
    self.source = source
    self.target = target
    self.type = type
    self.size = size
    self.message = message

q = queue.SimpleQueue()


inbox = None

turnOffWait = -1

def handler(source, target, type, size, message):
    global inbox

    # Watch out, logging via stdout to a console will give too low latency in handling uart messages.
    # Redirecting to disk gives a big improvement in that. Not logging handoffs is also a big improvement.
    if type != 0x00:
        q.put(Message(source, target, type, size, message))

    if target == 0x00:
        if len(message) != size:
            print(f"!!:SZ")
        elif crc(message) != message[-1:][0]:
            print(f"!!:CRC")
        else:
            inbox = message

def msgHex(value):
    return msg(bytes.fromhex(value))

def msg(value):
    message = add_crc(b'\x10' + value)

    first = True
    result = bytearray()
    for byte in message:
        result.append(byte)
        if not first and byte == 0x10:
            result.append(byte)
        first = False

    return result

def write(ser, message):
    ser.write(message)

def readMessage(ser):
    global inbox
    ser.timeout = 0.25
    while not inbox:
        byte = ser.read()
        if len(byte) == 0:
            return None
        messageParser.feed(byte)
    ret = inbox
    inbox = None
    return ret


def exchange(ser, message):
    write(ser, message)
    ret = readMessage(ser)
    if ret[3] != message[3]:
        print(f'Wrong reply, expected {message[3]:#04x}, got {ret[3]:#04x}')
    else:
        pass


def handleMessage(reply, ser):
    global turnOffWait
    if reply[0] == 0x10 and reply[1] == 0x00: # Handoff back to motor
        return True # Control back to us
    if reply[0] == 0x10 and reply[1] == 0x04 and reply[2] == 0xc0: # Ping from display
        write(ser, msgHex('c300')) # OK
        return False
    if reply[0] == 0x10 and reply[1] == 0x02 and reply[2] == 0x21 and reply[3] == 0x09 and reply[4] == 0x00: # Put data ok
        return True # Control back to us
    if reply[0] == 0x10 and reply[1] == 0x01:
        if reply[2] == 0x28 and reply[3] == 0x09: # PUT DATA
            write(ser, msgHex('22010900')) # OK
            return False
        elif reply[2] == 0x20 and reply[3] == 0x30: # TURN ON
            write(ser, msgHex('220030')) # OK
            return False
        elif reply[2] == 0x21 and reply[3] == 0x31: # TURN OFF
            turnOffWait = 20
            write(ser, msgHex('220031')) # OK
            return False
        elif reply[2] == 0x20 and reply[3] == 0x32: # ASSIST ON
            write(ser, msgHex('220032')) # OK
            return False
        elif reply[2] == 0x20 and reply[3] == 0x33: # ASSIST OFF
            write(ser, msgHex('220033')) # OK
            return False
        elif reply[2] == 0x21 and reply[3] == 0x34: # SET ASSIST LEVEL
            write(ser, msgHex('220034')) # OK
            return False
        elif reply[2] == 0x20 and reply[3] == 0x35: # CALIBRATE
            write(ser, msgHex('22013500')) # OK
            return False
        elif reply[2] == 0xc6 and reply[3] == 0x08 and reply[5] == 0xdf and reply[7] == 0x3f and reply[9] == 0x5e: # GET DATA
            write(ser, msgHex('c20a080080df00803f00005e02')) # OK
            return False
        elif reply[2] == 0x23 and reply[3] == 0x08 and reply[5] == 0x5c: # GET DATA
            write(ser, msgHex('220c0800405c081337100000000799')) # OK
            return False
        elif reply[2] == 0x22 and reply[3] == 0x08 and reply[5] == 0xdf: # GET DATA
            write(ser, msgHex('2204080000df00')) # OK
            return False
        elif reply[2] == 0x2d and reply[3] == 0x09: # PUT DATA
            write(ser, msgHex('22010900')) # OK
            return False

    print(f"UFO: {reply.hex()}")
    return False


messageParser = MessageParser(handler)

print("Ready..")


def logger():
    while True:
        m = q.get()
        printPacket(m.source, m.target, m.type, m.size, m.message)

def program():

    with serial.Serial('/dev/ttyUSB0', 9600) as ser:

        global turnOffWait
        ts = time.time()

        speed = 0
        dist = 0


        while True:

            # Wait till we receive a message.
            while True:
                ret = readMessage(ser)
                if not ret:
                    print('timeout!')
                else:
                    break
            # Handle the message, then read the next, until we're given control.
            while not handleMessage(ret, ser):
                ret = readMessage(ser)

            if turnOffWait >= 0:
                turnOffWait -= 1

            if turnOffWait == 0:
                exchange(ser, msgHex('210011'))

            ts2 = time.time()
            if ts2 > ts + 1:
                # speed += 1
                # speed %= 250
                dist += 100
                dist %= 10000
                write(ser, msgHex('210a0994c0' + speed.to_bytes(2, 'big').hex() + '08c1' + dist.to_bytes(4, 'big').hex())) # Status update (speed km/h*10,trip in 10m)
                ts = ts2
            else:
                write(ser, msgHex('20')) # HANDOFF to BMS

  
        print("Done..")

threading.Thread(target=logger).start()
threading.Thread(target=program).start()