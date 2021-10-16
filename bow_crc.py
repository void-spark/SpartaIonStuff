crcInit=0x07
crcPoly=0x42

def calc_crc(message):
  crc = crcInit

  for data in message:
    for i in range(8):
      f = ((crc ^ data) & 0x01)
      if f == 0x01:
        crc = crc ^ crcPoly
      crc = (crc >> 1) & 0x7F
      if f == 0x01:
        crc = crc | 0x80
      data = data >> 1
  return crc

def crc(message):
  return calc_crc(message[:-1])

def add_crc(message):
    crcVal = calc_crc(message)
    return message + bytes([crcVal])
