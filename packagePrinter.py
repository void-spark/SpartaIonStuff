from bow_crc import crc

def who(value):
  if value == 0x0C:
    return "DP"
  elif value == 0x04:
    return "PC"
  elif value == 0x02:
    return "BT"
  elif value == 0x00:
    return "MT"
  else:
    return bytes([value]).hex()

def printBlink(name, input, shift):
  val = (input >> shift) & 0x03 
  if val != 0x00:
    print(f"{name}", end='')
    if val == 0x01:
      print(f":FST", end='')
    if val == 0x02:
      print(f":SLW", end='')
    if val == 0x03:
      print(f":SOL", end='')
    print(f" ", end='')

def typeName(type):
  if type == 0x18:
    return "Battery level"

  if type == 0x1a:
    return "Max battery level"

  if type == 0x32:
    return "Battery serial#"

  if type == 0x38:
    return "Calibration A"

  if type == 0x3a:
    return "Calibration B"

  if type == 0x5b:
    return "Paired serial 1"

  if type == 0x5c:
    return "Paired serial 2"

  if type == 0x80:
    return "Total distance"

  if type == 0x8e:
    return "Time"

  return "Unknown"

def printGetData(message):
  data = message[4:-1]

  index = 0
  while True:
      array = (data[index] & 0x40) != 0
      more = (data[index] & 0x80) != 0

      if array:
          partSize = 3
      else:
          partSize = 2

      part = data[index:index + partSize]

      flags = part[0] & 0x7f
      type =  part[1]

      print(f" {bytes([flags]).hex()}:{bytes([type]).hex()}", end='')
      if array:
        print(f"[{part[2]}]", end='')
      print(f"({typeName(type)})", end='')

      if more:
          index += partSize
      else:
          break


def printPacket(source, target, type, size, message):
  print(f"tgt:{who(target)} typ:{type}", end='')
  if type == 0x00: # Collision prevention, 'you may send next'. Sent by one component, or the one mentioned sends the next one?
    print(f"        [{message[:1].hex()}-{message[1:2].hex()}-{message[-1:].hex()}]", end='')
    maySend = ...
  elif type == 0x03 or type == 0x04: # Ping/are you there? src and target, but no payload
    print(f" src:{who(source)} [{message[:1].hex()}-{message[1:3].hex()}-{message[-1:].hex()}]", end='')
  else:
    print(f" src:{who(source)} [{message[:1].hex()}-{message[1:3].hex()}-{message[3:-1].hex()}-{message[-1:].hex()}] [{message[3:-1].hex()}]", end='')

  if len(message) != size:
    print(f" SIZE MISMATCH", end='')

  if crc(message) != message[-1:][0]:
    print(f" CRC MISMATCH", end='')

  ## Generic
  if type == 0x04:
      print(f" - PING!", end='')
  if type == 0x03:
      print(f" - PONG!", end='')

  if type == 0x00:
      print(f" - HANDOFF", end='')

  if type == 0x01 or type == 0x02:

    if message[3] == 0x08:
      if type == 0x01:
        # [10-0123-08484d00-10] Always these 6 in sequence
        # [10-0123-08484d02-71] All 8484-4[de]-0[024] 00/02/04 is offset in array
        # [10-0123-08484d04-d2]
        # [10-0123-08484e00-54]
        # [10-0123-08484e02-35]
        # [10-0123-08484e04-96]
        print(f" - GET DATA {message[4:-1].hex()}", end='')
        printGetData(message)
      if type == 0x02:
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

    if message[3] == 0x09:
      if type == 0x01:
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

        # [10-0128-0994b009c414b1....-..] (from notes) die nächsten beiden Bytes Akku-Stand?!
        # [10-0128-0994b009c414b1010e-ca]
        # [10-0128-0994b009c414b1010e-ca]
        # [10-0128-0994b009c414b1010e-ca]
        # [10-0128-0994b009c414b100f1-86]
        # [10-0128-0994b009c414b100fa-b1]
        # [10-0124-0914b009c4-e0] Every second
        print(f" - PUT DATA {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 1
        # [10-0221-0900-ab] Befehl 09 wird immer mit Payload 0x00 quittiert

        # [10-2201-0900-d6] [0900] Befehl 09 wird immer mit Payload 0x00 quittiert
        print(f" - PUT DATA - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x30:
      if type == 0x01: # Payload: 0
        # [10-0120-30-14]
        print(f" - TURN ON {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-2200-30-8b]
        print(f" - TURN ON - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x31:
      if type == 0x01: # Payload: 1
        # [10-0121-3100-22]
        print(f" - TURN OFF {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-2200-31-1a]
        print(f" - TURN OFF - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x32:
      if type == 0x01: # Payload: 0
        # [10-0120-32-75]
        print(f" - ENABLE ASSIST {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-2200-32-ea]
        print(f" - ENABLE ASSIST - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x33:
      if type == 0x01: # Payload: 0
        # [10-0120-33-e4] 
        print(f" - DISABLE ASSIST {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-2200-33-7b]
        print(f" - DISABLE ASSIST - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x34:
      if type == 0x01: # Payload: 1
        print(f" - SET ASSIST LEVEL {message[4:-1].hex()}", end='')
        if message[4] == 0x01:
          # [10-0121-3401-7f] Value seems to be 01,02,03. That's too suspicious :)
          print(f" > ECO", end='')
        if message[4] == 0x02:
          print(f" > NORMAL", end='')
        if message[4] == 0x03:
          print(f" > POWER", end='')
      if type == 0x02: # Payload: 0
        # [10-2200-34-49]
        print(f" - SET ASSIST LEVEL - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x11:
      if type == 0x01: # Payload: 0
        # [10-2100-11-f0]
        print(f" - MOTOR OFF UPDATE {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-0220-11-6f] 
        print(f" - MOTOR OFF UPDATE - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x12:
      if type == 0x01: # Payload: 1
        # [10-2101-1201-41] // Right after telling the motor to turn on assistance
        # [10-2101-1200-d0] // Right after telling the motor to turn off assistance
        print(f" - ASSIST STATUS UPDATE (ON/OFF) {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-0220-12-9f]
        print(f" - ASSIST STATUS UPDATE (ON/OFF) - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x15:
      if type == 0x01: # Payload: 0
        # [10-2100-15-32]
        print(f" - MYSTERY BATTERY COMMAND 15 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-0220-15-ad]
        print(f" - MYSTERY BATTERY COMMAND 15 - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x04:
      if type == 0x01: # Payload: 0
        # [10-c120-04-d3] Also sent with CU2 sometimes, at an interval? Might precede 17 on CU3
        print(f" - MYSTERY DISPLAY COMMAND 04 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-22c0-04-61]
        print(f" - MYSTERY DISPLAY COMMAND 04 - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x17:
      if type == 0x01:
        print(f" - SHOW ERROR: E-00{message[4:5].hex()}", end='')
      if type == 0x02:
        print(f" - SHOW ERROR - OK", end='')

    if message[3] == 0x20:
      if type == 0x01: # Payload: 0
          # [10-c100-20-03]
          print(f" - GET DISPLAY SERIAL# {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 8
          # [10-02C8-200506000000002306-0A] (from notes, serial 0506 2306)
          # [10-02c8-201641100000000266-42] - my serial is actually 164110266, 9 chars, not 8 like some others
          print(f" - GET DISPLAY SERIAL# - OK {message[4:6].hex()} {message[10:12].hex()} ({message[4:-1].hex()})", end='')

    if message[3] == 0x22:
      if type == 0x01: # Payload: 1
          # Starts with a single 0x08, then cycles through values 0x00-0x0F. Every 100ms
          print(f" - BUTTON CHECK {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 2
          # Cycles through 0x0000-0x00FF. Sometimes repeats the last value. First byte changes if button pressed: 02: bottom, 01: top, 03: both
          print(f" - BUTTON CHECK - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x25:
      if type == 0x01: # Payload: 2
        # [10-c122-250408-84] Always 0408, always once when the display is turned on
        print(f" - MYSTERY DISPLAY COMMAND 25 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-22c0-25-29]
        print(f" - MYSTERY DISPLAY COMMAND 25 - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x26 or message[3] == 0x27:
      if type == 0x01:
        if message[3] == 0x26:
          print(f" - UPDATE DISPLAY(CU2): ", end='')
        if message[3] == 0x27:
          print(f" - UPDATE IDLE DISPLAY(CU2): ", end='')

        printBlink("OFF", message[4], 0)
        printBlink("ECO", message[4], 2)
        printBlink("NRM", message[4], 4)
        printBlink("POW", message[4], 6)

        printBlink("WRE", message[5], 0)
        printBlink("TOT", message[5], 2)
        printBlink("TRP", message[5], 4)
        printBlink("LIG", message[5], 6)

        printBlink("BAR", message[6], 0)
        printBlink("COM", message[6], 4)
        printBlink("KM", message[6], 6)

        print(f"{message[7]:02d}% ", end='')

        spd = message[8:10].hex()
        print(f"'{spd[1:3] + '.' + spd[3:]}' ", end='')
        print(f"'{message[10:13].hex()[1:].replace('c', ' ').replace('a', '-')}' ", end='')

      if type == 0x02: # Payload: 0
        if message[3] == 0x26:
          print(f" - UPDATE DISPLAY(CU2) - OK {message[4:-1].hex()}", end='')
        if message[3] == 0x27:
          print(f" - UPDATE IDLE DISPLAY(CU2) - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x28:
      if type == 0x01: # Payload: 13
        # [10-c12d-2800000000000000000000000000-a8]
        print(f" - UPDATE DISPLAY(CU3): {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 1
        # [10-22c1-2801-60]
        print(f" - UPDATE DISPLAY(CU3) - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x29:
      if type == 0x01: # Payload: 1
        # [10-c121-2916-b6] So far only once while playing with menu
        print(f" - MYSTERY DISPLAY COMMAND 29 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-22c0-29-2c] 
        print(f" - MYSTERY DISPLAY COMMAND 29 - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x1b:
      if type == 0x01:
        print(f" - CU3: CALIBRATE {message[4:-1].hex()}", end='')
      if type == 0x02:
        print(f" - CU3: CALIBRATE - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x1c:
      if type == 0x01:
        print(f" - CU3: SET LIGHT {message[4:-1].hex()}", end='')
      if type == 0x02:
        print(f" - CU3: SET LIGHT - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x1d:
      if type == 0x01:
        print(f" - CU3: SET ASSIST {message[4:-1].hex()}", end='')
      if type == 0x02:
        print(f" - CU3: SET ASSIST - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x01:
      if type == 0x01: # Payload: 0
        # [10-21c0-01-01] << Once, while playing with CU3 menu
        print(f" - MYSTERY BATTERY COMMAND 01 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 2
        # [10-c222-010202-03] [010202]
        print(f" - MYSTERY BATTERY COMMAND 01 - OK {message[4:-1].hex()}", end='')

    if message[3] == 0x14:
      if type == 0x01: # Payload: 1
        # [10-21c0-14-9f] Once or twice, a bit before turn on motor.
        print(f" - MYSTERY BATTERY COMMAND 14 {message[4:-1].hex()}", end='')
      if type == 0x02: # Payload: 0
        # [10-c220-14-2d]
        print(f" - MYSTERY BATTERY COMMAND 14 - OK {message[4:-1].hex()}", end='')

  print()



# 09 'put data' data types:
# [10-210a-09 94c0 0113 08c1 00000005  -04] 1001/0000 speed / trip(?) 4/8 = nibbles? c0/c1 is data type? bit 0 = other follows?
# [10-210a-09 9438 42f8 283a 3e789c11  -dd] 1001/0010 4/8 = nibbles? 38/3a is data type?
# [10-0128-09 94b0 09c4 14b1 0117      -51] 1001/0001 4/4 = nibbles? b0/b1 is data type? left is always 09c4(=2500) speed limit ???, right varies, tends to go lower over time, voltage? 
# [10-0124-09 14b0 09c4                -e0] 0001 4 = nibbles b0 is data type? same as above, only when not moved after fuse in (???) 0x09c4 = 2500


# 08 'get data' data types:
# request
# [10-0123-08 484d00-10] Always these 6 in sequence
# [10-0123-08 484d02-71] All 8484-4[de]-0[024]
# [10-0123-08 484d04-d2]
# [10-0123-08 484e00-54]
# [10-0123-08 484e02-35]
# [10-0123-08 484e04-96]
# response
# [10-220c-08 00 484d020000000000000000  -eb] 0100  4d is data type? 4x = array with elements of length x nibbles 02 = two elements
# [10-220c-08 00 484d020000000000000000  -eb] 0100  4d is data type? 
# [10-2204-08 00 484d00-e8]                   0100  4d is data type?
# [10-220c-08 00 484e020000000000000000  -3c] 0100  4e is data type?
# [10-220c-08 00 484e020000000000000000  -3c] 0100  4e is data type?
# [10-2204-08 00 484e00-ac]                         4e is data type?

# [10-2104-08 9438283a   -d7]
# [10-022b-08 00 9438 42f8 283a 3e789c11  -db]

# Data type 38/3a. Left value seems to wiggle, right seems to count up or down fast??
# 405a 3e6b0c51
# 4056 3e6d10ed 
#   -4   +2049C
#   -4  +132252

# 0003b1 (954)

# TOT1:05458
# TOT2:05467


# -|-|M|<|BT|MT|08| - GET DATA 4127 3e9135d4 1049703892 9516500
# -|-|M|>|MT|BT|09| - PUT DATA 4132 3e90fea6 1049689766 9502374  -14126 (17)
# -|-|M|<|BT|MT|08| - GET DATA 4132 3e90fea6 1049689766 9502374
# -|-|M|>|MT|BT|09| - PUT DATA 4130 3e90ccaf 1049676975 9489583  -12791 (13)
# -|-|M|<|BT|MT|08| - GET DATA 4130 3e90ccaf 1049676975 9489583
# -|-|M|>|MT|BT|09| - PUT DATA 412e 3e908bc1 1049660353 9472961  -16622 (10)
# -|-|M|<|BT|MT|08| - GET DATA 412e 3e908bc1 1049660353 9472961
# -|-|M|>|MT|BT|09| - PUT DATA 4130 3e9040cd 1049641165 9453773  -19188 (9)
# -|-|M|<|BT|MT|08| - GET DATA 4130 3e9040cd 1049641165 9453773
# -|-|M|>|MT|BT|09| - PUT DATA 4129 3e900932 1049626930 9439538  -14235 (11)
# -|-|M|<|BT|MT|08| - GET DATA 4129 3e900932 1049626930 9439538
# -|-|M|>|MT|BT|09| - PUT DATA 412b 3e8fcbe2 1049611234 9423842  -15696 (19)

# -|-|M|<|BT|MT|08| - GET DATA 405a 3e6b0c51 1047202897 7015505
# -|-|M|>|MT|BT|09| - PUT DATA 4056 3e6d10ed 1047335149 7147757 +132252 (954)

# -|-|M|>|MT|BT|09| - PUT DATA 42f8 3e789c11 1048091665 7904273
# -|-|M|<|BT|MT|08| - GET DATA 42f8 3e789c11 1048091665 7904273

# -|-|M|<|BT|MT|08| - GET DATA 403f 3e651da8 1046814120 6626728
# -|-|M|<|BT|MT|08| - GET DATA 4047 3e651da8 1046814120 6626728
# -|-|M|>|MT|BT|09| - PUT DATA 4045 3e651da8 1046814120 6626728
