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


def messageFor(type, source, target, message, tgt, src, cmd = None ):
  if (type == 0x01 and target == tgt and source == src) or (type == 0x02 and target == src and source == tgt ):
    if cmd == None or message[3] == cmd:
      return True
  return False

def formatMotorCommand(type, source, target, message):
  if not messageFor(type, source, target, message, 0x00, 0x02):
    return "---|---|"

  if message[3] == 0x30:
    if type == 0x01:
      return f"ON |---|"
    else:
      return f"OK |---|"

  elif message[3] == 0x31:
    if type == 0x01:
      return f"OFF|{message[4:-1].hex()} |"
    else:
      return f"OK |---|"

  elif message[3] == 0x32:
    if type == 0x01:
      return f"ASS|ON |"
    if type == 0x02:
      return f"OK |---|"

  elif message[3] == 0x33:
    if type == 0x01:
      return f"ASS|OFF|"
    if type == 0x02:
      return f"OK |---|"

  elif message[3] == 0x34:
    if type == 0x01:
      if message[4] == 0x01:
        return f"ASS|ECO|"
      if message[4] == 0x02:
        return f"ASS|NOR|"
      if message[4] == 0x03:
        return f"ASS|POW|"
    if type == 0x02:
      return f"OK |---|"

  else:
    return "---|---|"


def formatPutDataMotor(type, source, target, message):
  if not messageFor(type, source, target, message, 0x00, 0x02, 0x09):
    return "----|----|"

  if type == 0x01: # Payload: 4
    result = ""
    payload = message[4:-1]
    if payload[1] == 0xb0:
      result += f"{payload[2] * 0x100 + payload[3]:04d}|"
    if len(payload) > 4 and payload[5] == 0xb1:
      result += f"{(payload[6] * 0x100 + payload[7])/10:03.1f}|"
    else: 
      result += "----|"
    return result
  if type == 0x02: # Payload: 1
    # [10-2201-0900-d6] [0900] Befehl 09 wird immer mit Payload 0x00 quittiert
    return f"OK--|{message[4:-1].hex()}--|"


def formatPollDisplay(type, source, target, message):
  if not messageFor(type, source, target, message, 0x0C, 0x02, 0x22):
    return "--|--|--|"

  if type == 0x01: # Payload: 1
      return f"{message[4:-1].hex()}|--|--|"
  else:
      return f"--|{message[4:5].hex()}|{message[5:-1].hex()}|"
  

def formatUpdateDisplay(type, source, target, message):
  if not (messageFor(type, source, target, message, 0x0C, 0x02, 0x26) or
          messageFor(type, source, target, message, 0x0C, 0x02, 0x27)):
    return "---|---|---|---|---|---|---|--|--|----|-----|"

  result = ""
  if type == 0x01:
    if message[4] & 0x03 != 0:
      result += f"OFF|"
    if message[4] & 0x0C != 0:
      result += f"ECO|"
    if message[4] & 0x30 != 0:
      result += f"NRM|"
    if message[4] & 0xC0 != 0:
      result += f"POW|"

    if message[5] & 0x03 != 0:
      result += f"WRE|"
    else:
      result += f"---|"

    if message[5] & 0x0C != 0:
      result += f"TOT|"
    else:
      result += f"---|"

    if message[5] & 0x30 != 0:
      result += f"TRP|"
    else:
      result += f"---|"

    if message[5] & 0xC0 != 0:
      result += f"LIG|"
    else:
      result += f"---|"


    if message[6] & 0x03 != 0:
      result += f"BAR|"
    else:
      result += f"---|"

    if message[6] & 0x30 != 0:
      result += f"COM|"
    else:
      result += f"---|"

    if message[6] & 0xC0 != 0:
      result += f"KM|"
    else:
      result += f"--|"

    result += f"{message[7]:02d}|"
    spd = message[8:10].hex()
    result += f"{spd[1:3] + '.' + spd[3:]}|"
    result += f"{message[10:13].hex()[1:].replace('c', ' ').replace('a', '-')}|"

    return result

  else:
    return "OK |---|---|---|---|---|---|--|--|----|-----|"

def printPacketDense(source, target, type, size, message):
  if type == 0x00:
    return
    print(f"H|-|-|-|--|{who(target)}|", end='')
  elif type == 0x01:
    print(f"-|-|M|>|{who(source)}|{who(target)}|", end='')
  elif type == 0x02:
    print(f"-|-|M|<|{who(source)}|{who(target)}|", end='')
  elif type == 0x03:
    print(f"-|P|-|<|{who(source)}|{who(target)}|", end='')
  elif type == 0x04:
    print(f"-|P|-|>|{who(source)}|{who(target)}|", end='')
  else:
    print(f"{type}|-|-|-|{who(source)}|{who(target)}", end='')

  if crc(message) != message[-1:][0]:
    print(f" CRC MISMATCH", end='')

  if message[0] != 0x10:
    print(f" INVALID FIRST BYTE", end='')

  if len(message) != size:
    print(f" SIZE MISMATCH", end='')

  if type == 0x00:
    print(f"--|", end='')
    if len(message) != 3:
      print(f" INVALID SIZE", end='')
  elif type == 0x03 or type == 0x04:
    print(f"--|", end='')
    if len(message) != 4:
      print(f" INVALID SIZE", end='')
  else:
    print(f"{message[3:4].hex()}|", end='')
    # print(f" [{message[:1].hex()}-{message[1:3].hex()}-{message[3:-1].hex()}-{message[-1:].hex()}] [{message[3:-1].hex()}]", end='')

  ## TO MOTOR (always from batt)
  if (type == 0x01 and source == 0x02 and target == 0x00) or (type == 0x02 and source == 0x00 and target == 0x02):

    if message[3] == 0x08:
      if type == 0x01: # Payload: 3
        # [10-0123-08484d00-10] Always these 6 in sequence
        # [10-0123-08484d02-71] All 8484-4[de]-0[024] 00/02/04 is offset in array
        # [10-0123-08484d04-d2]
        # [10-0123-08484e00-54]
        # [10-0123-08484e02-35]
        # [10-0123-08484e04-96]
        print(f" - GET DATA {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 12/4
        # [10-220c-0800484d020000000000000000-eb] 02 is element count
        # [10-220c-0800484d020000000000000000-eb]
        # [10-2204-0800484d00-e8]                 00 is element count
        # [10-220c-0800484e020000000000000000-3c]
        # [10-220c-0800484e020000000000000000-3c]
        # [10-2204-0800484e00-ac]

        # [10-220c-0800484d0200000000000000df-83]
        # [10-220c-0800484d020000000000000000-eb]
        # [10-2204-0800484d00-e8]
        # [10-220c-0800484e0200000013000001ef-62]
        # [10-220c-0800484e020000000000000000-3c]
        # [10-2204-0800484e00-ac]

        # [10-220c-0800484d020000000000000292-5f]
        # [10-220c-0800484d020000000000000000-eb]
        # [10-2204-0800484d00-e8]
        # [10-220c-0800484e020000001300000589-d8]
        # [10-220c-0800484e020000000000000000-3c]
        # [10-2204-0800484e00-ac]

        # [10-220c-0800484d02000000030000039f-7d]
        # [10-220c-0800484d020000000500000009-60]
        # [10-2204-0800484d00-e8]
        # [10-220c-0800484e020000001800000799-ad]
        # [10-220c-0800484e02000000080000000e-12]
        # [10-2204-0800484e00-ac]

        # [10-220c-0800484d0200000003000003a0-9c]
        # [10-220c-0800484d020000000500000009-60]
        # [10-2204-0800484d00-e8]
        # [10-220c-0800484e0200000018000007a5-bc]
        # [10-220c-0800484e02000000080000000e-12]
        # [10-2204-0800484e00-ac]

        print(f" - GET DATA - OK {message[4:-1].hex()}", end='')

  ## TO Battery (always from motor)
  if (type == 0x01 and source == 0x00 and target == 0x02) or (type == 0x02 and source == 0x02 and target == 0x00):

    if message[3] == 0x08:
      if type == 0x01:
          # [10-2104-089438283a-d7] Always it seems Asks for 9438 and 283a?
          print(f" - GET DATA {message[4:-1].hex()}", end='')
      if type == 0x02:
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 42f8 283a 3e789c11-db] Repeated by the battery which wanted a new(?) style display
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 403f 283a 3e651da8-df] One for each log usually. At start of log, repeats data from last 09 command 
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4132 283a 3e90fea6-4c]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4130 283a 3e90ccaf-0e]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 412e 283a 3e908bc1-55]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4130 283a 3e9040cd-fd]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4129 283a 3e900932-45]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4127 283a 3e9135d4-48]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 405a 283a 3e6b0c51-c5]
          # tgt:MT typ:2 src:BT [10-022b-08 00 9438 4047 283a 3e651da8-85]
          print(f" - GET DATA - OK {message[7:9].hex()} {message[12:15].hex()} ({message[4:-1].hex()})", end='')

    if message[3] == 0x09:
      if type == 0x01: # Payload: 10
          # [10-210A-0994C000C708C100000006-D2] (from notes)
          # [10-210a-0994c0000008c100000000-15] Every second. byte 6+7 (left) is speed in km/h*10 so 0x09 is status update command?
          # [10-210a-0994c000bc08c1000000be-09] Bytes on the right look like trip(total km?) SINCE MOTOR POWER ON, in 10 m increments, left is speed??. (94)c0/(08)c1 might be data type? 
          # [10-210a-0994384132283a3e90fea6-4a] Uncommon, shutdown confirmation? 38/83 here total km? avg? At end of log, data will be repeated by next 08
          # [10-210a-0994384130283a3e90ccaf-08]
          # [10-210a-099438412e283a3e908bc1-53]
          # [10-210a-0994384130283a3e9040cd-fb]
          # [10-210a-0994384129283a3e900932-43]
          # [10-210a-099438412b283a3e8fcbe2-94]
          # [10-210a-0994384056283a3e6d10ed-8b]
          # [10-210a-0994384045283a3e651da8-21]
          print(f" - PUT DATA {message[6:8].hex()} {message[11:14].hex()} ({message[4:-1].hex()})", end='')
      if type == 0x02: # Payload: 1
          # [10-0221-0900-ab] Befehl 09 wird immer mit Payload 0x00 quittiert
          print(f" - PUT DATA - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x11:
      if type == 0x01:
        print(f" - MYSTERY BATTERY COMMAND 11 MOTOR OFF UPDATE {message[4:-1].hex()}", end='')
      if type == 0x02:
        print(f" - MYSTERY BATTERY COMMAND 11 MOTOR OFF UPDATE - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x12:
      if type == 0x01:
        print(f" - MYSTERY BATTERY COMMAND 12 ASSISTANCE STATUS UPDATE (ON/OFF) {message[4:-1].hex()}", end='')
      if type == 0x02:
        print(f" - MYSTERY BATTERY COMMAND 12 ASSISTANCE STATUS UPDATE (ON/OFF) - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x15:
      if type == 0x01:
        print(f" - MYSTERY BATTERY COMMAND 15 {message[4:-1].hex()}", end='') # Possibly we ran out of power?
      if type == 0x02:
        print(f" - MYSTERY BATTERY COMMAND 15 - OK {message[4:-1].hex()}", end='')

  ## TO DISPLAY (either from battery or motor)
  if (type == 0x01 and target == 0x0C) or (type == 0x02 and source == 0x0C):
    if (type == 0x01 and source == 0x02) or (type == 0x02 and target == 0x02):
      if message[3] == 0x25:
        if type == 0x01:
          print(f" - MYSTERY DISPLAY COMMAND 25 {message[4:-1].hex()}", end='')
        if type == 0x02:
          print(f" - MYSTERY DISPLAY COMMAND 25 - OK {message[4:-1].hex()}", end='')

    if (type == 0x01 and source == 0x00) or (type == 0x02 and target == 0x00):
      if message[3] == 0x20:
        if type == 0x01: # Payload: 0
            # [10-c100-20-03]
            print(f" - GET DISPLAY SERIAL# {message[4:-1].hex()}", end='')
        if type == 0x02: # Payload: 8
            # [10-02C8-200506000000002306-0A] (from notes, serial 0506 2306)
            # [10-02c8-201641100000000266-42] - my serial is actually 164110266, 9 chars, not 8 like some others
            print(f" - GET DISPLAY SERIAL# - OK {message[4:6].hex()} {message[10:12].hex()} ({message[4:-1].hex()})", end='')

  print(formatPollDisplay(type, source, target, message), end='')
  print(formatUpdateDisplay(type, source, target, message), end='')

  print(formatPutDataMotor(type, source, target, message), end='')

  print(formatMotorCommand(type, source, target, message), end='')

  print()

