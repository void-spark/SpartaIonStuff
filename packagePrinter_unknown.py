from bow_crc import crc

def who(value):
  if value == 0x0C:
    return "DP"
  elif value == 0x02:
    return "BT"
  elif value == 0x00:
    return "MT"
  else:
    return bytes([value]).hex()


def printRawMessage(source, target, type, message):
  print(f"tgt:{who(target)} typ:{type}", end='')
  if type == 0x00:
    print(f"        [{message[:1].hex()}-{message[1:2].hex()}-{message[-1:].hex()}]", end='')
  elif type == 0x03 or type == 0x04:
    print(f" src:{who(source)} [{message[:1].hex()}-{message[1:3].hex()}-{message[-1:].hex()}]", end='')
  else:
    print(f" src:{who(source)} [{message[:1].hex()}-{message[1:3].hex()}-{message[3:-1].hex()}-{message[-1:].hex()}] [{message[3:-1].hex()}]", end='')


def printPacketUnknown(source, target, type, size, message):

  if len(message) != size:
    printRawMessage(source, target, type, message)
    print(f" SIZE MISMATCH", end='')
    print()
    return

  if crc(message) != message[-1:][0]:
    printRawMessage(source, target, type, message)
    print(f" CRC MISMATCH", end='')
    print()
    return

  ## Generic
  if type == 0x00 and (target == 0x00 or target == 0x02 or target == 0x04 or target == 0x06 or target == 0x08 or target == 0x0a): # HANDOFF
    return

  if type == 0x04 and (source == 0x00 or source == 0x02 or source == 0x0c) and (target == 0x00 or target == 0x02 or target == 0x04 or target == 0x06 or target == 0x08 or target == 0x0a or target == 0x0c): # PING
    return

  if type == 0x03  and (source == 0x00 or source == 0x02 or source == 0x0c) and (target == 0x00 or target == 0x02 or target == 0x0c): # PONG
    return


  ## TO MOTOR (always from batt)
  if (type == 0x01 and source == 0x02 and target == 0x00) or (type == 0x02 and source == 0x00 and target == 0x02):

    if message[3] == 0x08: # GET DATA 
      if type == 0x01 and (size - 5) == 3 and message[4] == 0x48 and (message[5] == 0x4d or message[5] == 0x4e) and (message[6] == 0x00 or message[6] == 0x02 or message[6] == 0x04):
        return
      if type == 0x02: # Payload: 12/4
        if message[4] == 0x00 and message[5] == 0x48 and (message[6] == 0x4d or message[6] == 0x4e):
          if message[7] == 0x02 and (size - 5) == 12:
            val1 = int.from_bytes(message[8:12], "big")
            val2 = int.from_bytes(message[12:16], "big")
            return
          if message[7] == 0x00 and (size - 5) == 4:
            return

    if message[3] == 0x09: # PUT DATA
      if type == 0x01:
        if (size - 5) == 4 and message[4:8].hex() == '14b009c4':
          return
        if (size - 5) == 8 and message[4:6].hex() == '94b0' and message[8:10].hex() == '14b1':
          limiter = int.from_bytes(message[6:8], "big")
          voltage = int.from_bytes(message[10:12], "big")
          if voltage >= 20 * 10 and voltage <= 28 * 10 and limiter >= 500 and limiter <= 2500: # Between 20.0V and 28.0V, 'limiter' 2500-600
            return
      if type == 0x02 and (size - 5) == 1 and message[4] == 0:
        return

    if message[3] == 0x30: # ON
      if type == 0x01 and (size - 5) == 0:
        return
      if type == 0x02 and (size - 5) == 0:
        return

    if message[3] == 0x31: # OFF
      if type == 0x01 and (size - 5) == 1 and (message[4] == 0 or message[4] == 1):
        return

      if type == 0x02 and (size - 5) == 0:
        return

    if message[3] == 0x32: # ENABLE ASSIST 
      if type == 0x01 and (size - 5) == 0:
        return
      if type == 0x02 and (size - 5) == 0:
        return

    if message[3] == 0x33: # DISABLE ASSIST 
      if type == 0x01 and (size - 5) == 0:
        return
      if type == 0x02 and (size - 5) == 0:
        return      

    if message[3] == 0x34: # SET ASSIST LEVEL
      if type == 0x01 and (size - 5) == 1  and (message[4] == 1 or message[4] == 2 or message[4] == 3):
        return
      if type == 0x02 and (size - 5) == 0:
        return      

  ## TO Battery (always from motor)
  if (type == 0x01 and source == 0x00 and target == 0x02) or (type == 0x02 and source == 0x02 and target == 0x00):

    if message[3] == 0x08: # GET DATA 
      if type == 0x01 and (size - 5) == 4 and (message[4:8].hex() == '9438283a'):
        return
      if type == 0x02 and (size - 5) == 11 and message[4] == 0x00 and message[5:7].hex() == "9438" and message[9:11].hex() == "283a":
        return

    if message[3] == 0x09: # PUT DATA 
      if type == 0x01 and (size - 5) == 10 and message[4:6].hex() == "94c0" and message[8:10].hex() == "08c1":
        speed = int.from_bytes(message[6:8], "big")
        distance = int.from_bytes(message[10:14], "big")
        if speed <= 35 * 10 and distance <= 200 * 100: # Speed < 35km/h, Distance < 200km
          return        
      if type == 0x01 and (size - 5) == 10 and message[4:6].hex() == "9438" and message[8:10].hex() == "283a":
        return
      if type == 0x02 and (size - 5) == 1 and message[4] == 0:
        return

    if message[3] == 0x11: # MYSTERY BATTERY COMMAND 11
        if type == 0x01 and (size - 5) == 0:
          return
        if type == 0x02 and (size - 5) == 0:
          return

    if message[3] == 0x12: # MYSTERY BATTERY COMMAND 12
        if type == 0x01 and (size - 5) == 1 and (message[4] == 0 or message[4] == 1):
          return
        if type == 0x02 and (size - 5) == 0:
          return

    if message[3] == 0x15: # MYSTERY BATTERY COMMAND 15
        if type == 0x01 and (size - 5) == 0:
          return
        if type == 0x02 and (size - 5) == 0:
          return

  ## TO DISPLAY (either from battery or motor)
  if (type == 0x01 and target == 0x0C) or (type == 0x02 and source == 0x0C):
    if (type == 0x01 and source == 0x02) or (type == 0x02 and target == 0x02):

      if message[3] == 0x04: # PING??
        if type == 0x01 and (size - 5) == 0:
          return
        if type == 0x02 and (size - 5) == 0:
          return

      if message[3] == 0x25: # MYSTERY DISPLAY COMMAND 25
        if type == 0x01 and (size - 5) == 2 and (message[4] == 0x04 or message[4] == 0x08):
          return
        if type == 0x02 and (size - 5) == 0:
          return

      if message[3] == 0x26: # UPDATE DISPLAY
        if type == 0x01 and (size - 5) == 9: # Payload: 9
          # TODO: Check actual content
          return
        if type == 0x02 and (size - 5) == 0:
          return      

      if message[3] == 0x27: # SET DISPLAY DEFAULT
        if type == 0x01 and (size - 5) == 9: # Payload: 9
          # TODO: Check actual content
          return
        if type == 0x02 and (size - 5) == 0:
          return      

      if message[3] == 0x22: # BUTTON CHECK
        if type == 0x01 and (size - 5) == 1  and (message[4] == 0x80 or (message[4] >= 0x00 and message[4] <= 0x0f)):
          return
        if type == 0x02 and (size - 5) == 2 and (message[4] == 0x00 or message[4] == 0x01 or message[4] == 0x02 or message[4] == 0x03) and (message[5] >= 0x00 and message[5] <= 0xff):
          return

    if (type == 0x01 and source == 0x00) or (type == 0x02 and target == 0x00):
      if message[3] == 0x20: # GET DISPLAY SERIAL# 
        if type == 0x01 and (size - 5) == 0:
          return
        if type == 0x02 and (size - 5) == 8:
          return

  printRawMessage(source, target, type, message)
  print()
