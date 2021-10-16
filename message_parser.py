from bow_crc import crc

class MessageParser:
    cnt = 0
    target = None
    source = None
    type = None
    size = None
    message = None
    escaping = False

    def __init__(self, handler):
        self.handler = handler

    def feed(self, byte):
        input = b''
        if(self.escaping):
            input += b'\x10'
            if byte[0] != 0x10:
                input += byte
                # Unescaped 0x10, reset
                if self.cnt != 0:
                    if self.message:
                        print(f"Incomplete: {self.message.hex()} crc:{crc(self.message):#04x}")
                    self.cnt = 0
                    self.target = None
                    self.source = None
                    self.type = None
                    self.size = None
                    self.message = None
            self.escaping = False
        elif byte[0] != 0x10:
            input += byte
        else:
            self.escaping = True
            return

        for value in input:
            low = value & 0x0F
            high = value >> 4

            if self.cnt == 0:
                if value == 0x00:
                    # Ignore single '00' with no leading '10'
                    continue
                self.type = None
                self.size = None
                self.message = b''
            elif self.cnt == 1:
                self.target = high
                self.type = low
            elif self.cnt == 2:
                if self.type == 0x00:
                    self.size = 3
                else:
                    self.source = high
                    if self.type == 0x03 or self.type == 0x04:
                        self.size = 4
                    else:
                        self.size = low + 5

            self.message += bytes([value])

            self.cnt += 1

            if self.cnt > 2 and self.cnt == self.size:
                self.handler(self.source, self.target, self.type, self.size, self.message)

                self.cnt = 0
