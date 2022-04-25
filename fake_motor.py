#!/usr/bin/env python3
import sys
import time
import asyncio
import serial_asyncio
from bow_crc import add_crc
from packagePrinter import printPacket
from message_parser import MessageParser

queue = asyncio.Queue()

def handler(source, target, type, size, message):
    printPacket(source, target, type, size, message)
    if target == 0x00:
        queue.put_nowait(message)

async def setup():
    reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyUSB1', baudrate=9600)
    # reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    print("Starting..")

    messageParser = MessageParser(handler)

    asyncio.ensure_future(poller(writer))

    while (byte := await reader.read(1)):
        print(f"[{byte.hex()}]", end='')
        sys.stdout.flush()
        messageParser.feed(byte)

async def poller(writer):
    ts = time.time()

    speed = 0
    dist = 0

    while True:
        # await asyncio.sleep(0.1)
    
        while not await handleBmsMessage(writer):
            pass
        
        while not queue.empty():
            reply = queue.get_nowait()
            print(f'Flushed {reply.hex()}')

        ts2 = time.time()
        if ts2 > ts + 1:
            speed += 1
            speed %= 250
            dist += 100
            dist %= 10000
            await write(writer, msgHex('210a0994c0' + speed.to_bytes(2, 'big').hex() + '08c1' + dist.to_bytes(4, 'big').hex())) # Status update (speed 100m/s,trip in 10m)
            ts = ts2
        else:
            await write(writer, msgHex('20')) # HANDOFF to BMS

    print("Done..")

async def exchange(writer, message):
    while not queue.empty():
        reply = queue.get_nowait()
        print(f'Flushed {reply.hex()}')
    await write(writer, message)
    reply = await queue.get()
    if reply[3] != message[3]:
        print(f'Wrong reply, expected {message[3]:#04x}, got {reply[3]:#04x}')
    else:
        print(f'Received {reply.hex()} state: exchange')

async def write(writer, message):
    writer.write(message)
    await writer.drain()

async def handleBmsMessage(writer):
    reply = await queue.get()
    # print(f'Received {reply.hex()} state: handle BMS message')
    if reply[0] == 0x10 and reply[1] == 0x00: # Handoff back to motor
        return True # Control back to us
    if reply[0] == 0x10 and reply[1] == 0x02 and reply[2] == 0x21 and reply[3] == 0x09 and reply[4] == 0x00: # Put data ok
        return True # Control back to us
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x28 and reply[3] == 0x09: # PUT DATA
        await write(writer, msgHex('22010900')) # OK
        return False
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x20 and reply[3] == 0x30: # TURN ON
        await write(writer, msgHex('220030')) # OK
        return False
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x21 and reply[3] == 0x31: # TURN OFF
        await write(writer, msgHex('220031')) # OK
        return False
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x20 and reply[3] == 0x32: # ASSIST ON
        await write(writer, msgHex('220032')) # OK
        return False
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x21 and reply[3] == 0x34: # SET ASSIST LEVEL
        await write(writer, msgHex('220034')) # OK
        return False
    elif reply[0] == 0x10 and reply[1] == 0x01 and reply[2] == 0x20 and reply[3] == 0x33: # ASSIST OFF
        await write(writer, msgHex('220033')) # OK
        return False


def msgHex(value):
    # print(f'Send: {value}')
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

    print(f'Sent: {result.hex()}')
    return result


loop = asyncio.get_event_loop()
asyncio.ensure_future(setup())
loop.run_forever()
