#!/usr/bin/env python3
import asyncio
import serial_asyncio
from bow_crc import add_crc
from packagePrinter import printPacket
from message_parser import MessageParser

IDLE = 0
ACTIVE = 1

# Timeout on most commands, 225ms?
# Timeout on '4' commands, 57ms?

queue = asyncio.Queue()

def handler(source, target, type, size, message):
    # if not (((type == 0x01 and target == 0x0C) or (type == 0x02 and source == 0x0C)) and message[3] != 0x22 and message[3] != 0x26):
    #     cnt=0
    #     continue
    printPacket(source, target, type, size, message)
    if target == 0x02 and size > 1:
        queue.put_nowait(message[3])

async def setup():
    reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyUSB0', baudrate=9600)

    state = IDLE

    print("Ready..")

    while (byte := await reader.read(1)):
        if(state == IDLE and byte[0] == 0x00):
            asyncio.ensure_future(poller(writer))
            state = ACTIVE
            messageParser = MessageParser(handler)

        if(state == ACTIVE):
            messageParser.feed(byte)

async def poller(writer):
    step = 0
    count = 0
    kmh = 0
    battery = 100
    level = 0x00
    blink = 0x01
    # TODO: Start with 0x80 button message, and wait for first reply?
    # TODO: Mystery message 04??
    # TODO: Mystery message 25??
    while True:
        await asyncio.sleep(0.1)

        await exchange(writer, msg(bytes.fromhex('c12122') + bytes([count])))

        if(step == 9):
            step = 0

            # Assist:
            # off = 	0x03  0000 0011
            # eco = 	0x0C  0000 1100
            # normal =	0x30  0011 0000
            # power = 	0xC0  1100 0000

            # Segments-1:
            # wrench = 	0x03  0000 0011
            # total = 	0x0C  0000 1100
            # trip =	0x30  0011 0000
            # light = 	0xC0  1100 0000 (backlight on only if not blink)

            # Segments-2:
            # bars =          0x03  0000 0011 (last bar blinks if blink is set)
            # comma (lower) = 0x30  0011 0000
            # km =            0xC0  1100 0000

            # fast blink = 01
            # slow blink = 10
            # no blink  = 11

            # numbers are 0-9, a='-', b='b', c=' ', d='d', e='e', f='f'

            # Nibble between kmh and km seems to affect if km is shown (c=no, f=yes)


            segments1 = 0b11111111
            segments2 = 0b11110001

            assist = blink
            assist <<= level * 2

            km = kmh
            print(blink)
            print(level)
            print(assist)
            await exchange(writer, msgHex(f'c12926{assist:02x}{segments1:02x}{segments2:02x}{battery:02x}c{kmh:1x}{kmh:1x}{kmh:1x}f{km:1x}{km:1x}{km:1x}{km:1x}{km:1x}'))

            kmh += 1
            kmh %= 0x10

            battery -= 1
            if battery < 0:
                battery = 100

            if kmh % 4 == 0:
                level += 1
                if level == 0x04:
                    level = 0x00
                    blink += 1
                    if blink == 0x04:
                        blink = 0x01

        else:
            step += 1
        count += 1
        count %= 0x10


async def exchange(writer, message):
    while not queue.empty():
        reply = queue.get_nowait()
        print(f'Flushed {reply:#04x}')
    writer.write(message)
    await writer.drain()
    reply = await queue.get()
    if reply != message[3]:
        print(f'Wrong reply, expected {message[3]:#04x}, got {reply:#04x}')
    else:
        print(f'Received {reply:#04x}')    

def msgHex(value):
    print(value)
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

    print(result.hex())
    return result


loop = asyncio.get_event_loop()
asyncio.ensure_future(setup())
loop.run_forever()
