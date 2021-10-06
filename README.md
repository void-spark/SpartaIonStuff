# Bus
All components of the bike are connected with a single wire bus developed by 3T, which they call the Bow-Bus.

This bus is held high to 24v by the BMS, components can send messages by pulling the bus low to gnd.

The protocol in use is basic 9600 baud serial. The only special thing is that instead of two seperate wires, each component has both sending and receiving connected to the same bus. This means that some kind of collission avoidance is needed to prevent garbage on the bus. This is done but the components taking turns sending messages, and always ending with a message which lets another component know it can send a message.

If the bike is idle/in low power mode, there is no communication on the bus. To wake up the bus a single '0x00' byte is sent when a button is pressed on the display.

# Message structure
Each message starts with a '0x10' byte, except for the single '0x00' wake up byte.
If a message contains a '0x10' value, it is escaped by using two '0x10' values.

The last byte of a message is always a crc calculated over all preceding bytes of the message (including the '0x10').

The '0x10' byte is always followed by one or two header bytes which indicate the type, source, target, and length of the message, and optionally a payload which starts with a command byte, followed by data bytes.

# Message types
There a five message types, each indicated by the value of the second nibble of the second byte:
- '0' - A message to let another component know it is it's turn to send a message to the bus. Only contains a single header byte with the target in the first nibble, and type (0) in the second nibble.
- '4' - A message with no payload similar to a 'ping' (ICMP echo). Always contains two header bytes. The first nibble holds the target, the second nibble the type (4), the third nibble the source (to which the reply should be sent), and the last nibble is always 0.
- '3' - The reply message to a '4'/'ping' message. Same structure except for the type being '3'.
- '1' - A message with a payload. Always contains two header bytes. The first nibble holds the target, the second nibble the type (1), the third nibble the source (to which the reply should be sent), the fourth nibble is the size of the payload after the command byte. After the header there is always a command byte, followed by the actual payload (which can be empty).
- '2' - The reply message to a '1' message. Same structure except for the type being '2'. The command byte is always the same as in the request message.

Every message type has a target, which much send the next message on the bus. If it fails to do so another component will send a message after a timeout has passed.

Let's have some examples, we'll ignore the first (0x10) and last (crc) byte for each:

'0' / handoff message: `[10-20-68]`
1. '0x20', first nibble indicates target (2), second the type (0)

'4' / ping message: `[10-0420-cc]`
1. '0x04', first nibble indicates target (0), second the type (4)
2. '0x20', first nibble indicates source (2), second is always 0

'3' / pong message: `[10-2300-ab]`
1. '0x23', first nibble indicates target (2), second the type (3)
2. '0x00', first nibble indicates source (0), second is always 0

'1' / message: `[10-c121-2203-0e]`
1. '0xc1', first nibble indicates target (c), second the type (1)
2. '0x21', first nibble indicates source (2), second is payload length (1)
3. '0x22', command byte (22)
4. '0x03', first payload byte

'2' / message: `[10-22c2-220014-94]`
1. '0x22', first nibble indicates target (2), second the type (2)
2. '0xc2', first nibble indicates source (c), second is payload length (2)
3. '0x22', command byte (22)
4. '0x00', first payload byte
5. '0x14', second payload byte

# Devices
- '0' Motor controller
- '2' Battery managment system
- '4' Unknown, don't have it :)
- '6' Unknown, don't have it :)
- '8' Unknown, don't have it :)
- 'A' Unknown, don't have it :)
- 'C' Display 

# Commands
- `08` Get data, requests specific data from the target. The request and response payload are specially structured.
- `09` Put data, sends data to the target. Request payload is specially structured, response is always a single byte (00, but may hold an error code?)
- `11` Battery command with no payload in request/response. Sent from motor to battery just after telling the motor to go off.  
Could be a confirmation?
- `12` Battery command with a single byte payload (00 or 01), and no response payload. 01 Sent from motor to battery just after telling the motor to turn on assist, 00 just after off.  
Could be a confirmation?
- `20` Get (display) serial number. Payload is empty, reply payload holds the serial number.
- `22` Display unit button check. 1 byte payload with a incrementing number (00-0F). Reply has two bytes, with the first being the button status, and the second another incrementing number (00-FF)  
Not sure what the incrementing numbers are for, but as long as you increment them for each message everything seems to work.
- `25` Always sent to display when coming out of idle. Payload is always `0408`. Reply always empty.  
Not sure what it means.
- `26` Display update, 9 byte payload which sets icons/numbers on the display. Reply always empty.
- `27` Display update (default). Same as `26`, but (I think) it sets what to display when the regular updates stop.
- `30`: Motor command with no payload in request/response: Turn on
- `31`: Motor command with a single byte payload (00), and no response payload: Turn off
- `32`: Motor command with no payload in request/response: Enable assist
- `33`: Motor command with no payload in request/response: Disable assist
- `34`: Motor command with a single byte payload (01,02,03), and no response payload: Set assist level

# Messages to display

The display only reacts to messages sent to it, except for when it sends a '0' byte to wake up the system.
Almost all messages sent to the display are sent by the BMS.
The only exception is the message the motor sends to get the serial number of the display.


## `22` Get serial
This message is sent by the Motor to the display.
Sent some time after waking up the system usually.
The request is empty. The display responds with it's serial number, as 16 digits.
If the sticker has 8 numbers, the first 4 are at the beginning of the serial, and the last are at the end of the serial.
If the sticker has 9 numbers, the first 5 are at the beginning of the serial, and the last are at the end of the serial.

Full examples:
- `[10-c100-20-03]` - Request from Motor to BMS.
- `[10-02C8-200506000000002306-0A]` - Response for sticker '0506 2306', payload '0506000000002306'
- `[10-02c8-201641100000000266-42]` - Response for sticker '164110266', payload '1641100000000266'

## `25` Mystery display message
This message is sent by the BMS to the display.
It is sent once shortly after the system wakes up.
The request payload is always '0408', and the response has no payload.
It's not usually the very first message sent to the display.
Usually there have already been display button polling messages (22) and default display messages (26).
It does always seem to be sent before any set display message is sent (27)
Testing shows it's not actually required for the display to work.
Maybe it sets the timeout after a display update command, before the display reverts to the default screen?

Full examples:
- `[10-c122-250408-84]` - Request from BMS to display, payload '0408'.
- `[10-22c0-25-29]` - Response from display to BMS.



# Messages to bms


# Messages to motor controller


