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
- `04` Might be a ping of sorts? Only seen sent from battery to display with no payloads in request/response. Only seen it used while the motor is turned off.
- `08` Get data, requests specific data from the target. The request and response payload are specially structured.
- `09` Put data, sends data to the target. Request payload is specially structured, response is always a single byte (00, but may hold an error code?)
- `11` Battery command with no payload in request/response. Sent from motor to battery just after telling the motor to go off.  
Could be a confirmation?
- `12` Battery command with a single byte payload (00 or 01), and no response payload. 01 Sent from motor to battery just after telling the motor to turn on assist, 00 just after off.  
Could be a confirmation?
- `15` Not sure, seen only once from motor to battery, short before turning off the motor. No payloads in request/response. 
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

## `04` Mystery display message
This message is sent by the BMS to the display and has no payload in request or response.
This message isn't seen often, and seems to only be sent when the motor has been turned off.
Maybe some ping, or keepalive?
Full examples:
- `[10-c120-04-d3]` - Request from BMS to display.
- `[10-22c0-04-61]` - Response from display to BMG.

## `20` Get serial
This message is sent by the Motor to the display.
Sent some time after waking up the system usually.
The request is empty. The display responds with it's serial number, as 16 digits.
If the sticker has 8 numbers, the first 4 are at the beginning of the serial, and the last are at the end of the serial.
If the sticker has 9 numbers, the first 5 are at the beginning of the serial, and the last are at the end of the serial.

Full examples:
- `[10-c100-20-03]` - Request from Motor to display.
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

## `26` Update display
This message is sent by the BMS to the display.
The payload is always 9 bytes, which contains the different segments and values to show on the display.

For several segments there's a 2 bit value, which encodes blinking:
- `00`: Off
- `01`: Fast blink
- `10`: Slow blink
- `11`: No blink (on)

For the two numeric display the hex values of each nibble are used as the number for the digit,
additionally the remaining values are  mapped as follows:
- `a`: '-' (dash)
- `b`: 'b'
- `c`: ' ' (space)
- `d`: 'd'
- `e`: 'e'
- `f`: 'f'

The bytes are used as follows
- byte 0: Power level (2 bits per option to indicate blinking)
  - bit 0-1 (0x03): Off
  - bit 2-3 (0x0c): Eco
  - bit 4-5 (0x30): Normal
  - bit 6-7 (0xc0): Power
- byte 1: Segments 1 (2 bits per option to indicate blinking)
  - bit 0-1 (0x03): Wrench
  - bit 2-3 (0x0c): Total
  - bit 4-5 (0x30): Trip
  - bit 6-7 (0xc0): Light (Also turns on the backlight, if not set to blinking)
- byte 2: Segments 2 (2 bits per option to indicate blinking)
  - bit 0-1 (0x03): Bars (last bar blinks if blinking is set)
  - bit 4-5 (0x30): Comma
  - bit 6-7 (0xc0): Km
- byte 3: Battery left. Numeric value 0-100 as percentage of the amount of bars to show.
- byte 4-5: 3 digits of km/h display. Leftmost nibble seems unused and usually is set to 'c'.
- byte 6-8: 5 digits of km display. Leftmost nibble seems unused and usually is set to 'f'.

Full examples:
- `[10-c129-260c0cc361c000f09104-65]` - Request from BMS to display, 'eco', speed '00.0', total km '09104', bars 97%.
- `[10-c129-260c30c361c000fcccc0-c9]` - Request from BMS to display, 'eco', speed '00.0', trip km '    0', bars 97%.
- `[10-22c0-26-d9]` - Response from display to BMS.

## `27` Set default display
This message is sent by the BMS to the display.
The payload is always 9 bytes, which contains the different segments and values to show on the display.

The content is pretty much identical to a `26` message, but this seems to set a persistent default.
The only difference with a `26` message is the left two bytes of the 'unused' left nibble for each decimal value to show is `00` instead of `11`.
So:
- byte 4-5: 3 digits of km/h display. Leftmost nibble seems unused and usually is set to '0'.
- byte 6-8: 5 digits of km display. Leftmost nibble seems unused and usually is set to '3'.

Full examples:
- `[10-c129-270330c00000003cccc0-d4]` - Request from BMS to display, 'off', speed '00.0', trip km '    0', bars 0%.
- `[10-22c0-27-48]` - Response from display to BMS.

## `22` Poll buttons
This message is sent by the BMS to the display.
It is usually sent once every 100ms.
The first request message after the system waking up always has '80' as payload.
After that request messages cycle through values 0x00-0x0f consistently.
Respone messages are two bytes. The first is '00','01','02' or '03', depending on whether the top, bottom, or both buttons are pressed. The second byte seems to cycle through 0x00-0xff. But the pattern seems different among systems/displays. One shows an increment of 1 most of the time, sometimes skipping or repeating a value. Another shows much bigger more irregular steps, in the 20-50 range (at a glance).

Full examples:

- `[10-c121-2280-5f]` - First button poll message, payload '80'
- `[10-22c2-220001-0a]` - Button poll response, no button pressed, payload '0001'
- `[10-c121-220b-c9]` - Later button poll message, payload '0b'
- `[10-22c2-2202de-db]` - Button poll response, bottom button pressed, payload '02de'

# Messages to bms


# Messages to motor controller
Messages to the motor are always sent by the BMS.
Other then the messages described below, these can also be `0` handoff, or `4` ping messages.
When the motor is on, the BMS and motor generally take turns in sending messages, using the handoff message to return control to the other.

## `08` Get data
This message is sent by the BMS to the motor.
The `08` messages seem to always be a request for data from source to target, with the requesting data being sent back in the result.
The data requested and returned seems to be structured, the request specifies which data to get.
For the request from the BMS to the motor the structure of the data actually seems to be a sort of array, being retrieved in multiple messages.
Request payload is in the form `48-4[de]-0[024]`.
The right nibble of the first byte probably gives the length of a single array element in nibbles, the left nibble might specify it's an array.
The next byte is probably the value to be retrieved, either `4d` or `4e`. The last byte seems to be an index into the array, 0, 2 or 4.
The response is in the form `00-48-4[de]-02-xxxxxxxxyyyyyyyy` or `00-48-4[de]-00`.
The first byte is always 0, not sure why its there.
The second byte seems to match the first value of the request, so `48` again. Same for the third byte, `4[de]`.
The next byte seems to indicate the array element count returned, either 2 or or 0.
After that there's the actual array values. For both `4d` and `4e` there's 4 values of 4 bytes each.
Both `4d` and `4e` are normally requested after each other. So far I'm not sure yet what they mean yet.
The values are usually not that big, often also 0. The second value in each array is usually the largest,
and interestingly that value in `4e` is usually very roughly two times as big as the same value in `4d`.

Full examples:
- `[10-0123-08484d00-10]` - Request elements of array value `4d`, offset 0
- `[10-220c-0800484d02000000030000039f-7d]` - Response with 2 elements of array value `4d`
- `[10-0123-08484d02-71]` - Request elements of array value `4d`, offset 2
- `[10-220c-0800484d020000000500000009-60]` - Response with 2 elements of array value `4d`
- `[10-0123-08484d04-d2]` - Request elements of array value `4d`, offset 4
- `[10-2204-0800484d00-e8]` - Response with 0 elements of array value `4d`

## `09` Put data
This message is sent by the BMS to the motor.
The `09` messages seem to always be a push of data from source to target.
The data pushed seems to be structured, and contain a type per value.
The response seems to always be `00`, maybe that's an error code, where `00` is ok?
The request payload to the motor always seems to be in the form: `94-b0-xxxx-14-b1-xxxx`.
The b0 and b1 values are likely the types for the two contained values.
The xxxx parts are the actual values.
The right nibble of the `94` and `14` values are likely the length of the values, in nibbles.
The left nibble is probably some bit flags, with the leftmost bit indicating if there's a value following the current one.
This can be seen in the occasional message where the second value is missing, which has payload: `14-b0-xxxx`
So far the b1 (right) value looks like the battery voltage in 0.1 volt precision.
The b0 (left) value is almost always 2500. I've only seen it change when the battery is getting very low (0668, 0514, 1287, 0990 are some values).
One though is it might be the speed limit for the motor (25km/h is the legal limit here), but the other values seem very low for that.

Full examples:

- `[10-0128-0994b009c414b100f1-86]` - Push data message to motor, b0:2500 b1:0241 (24.1v)
- `[10-0124-0914b009c4-e0]` - Push data message to motor with only value b0:2500
- `[10-2201-0900-d6]` - Ok response from motor

## `30` Turn on
This message is sent by the BMS to the motor.
There is no payload in either the request or response.
It's sent usually very shortly after initially pressing the lower button (setting ECO mode), or turning on the display by just riding the bike.
Normally the motor does not send any messages before receiving this message.
Best guess so far it's a 'on' command of sorts for the motor, taking it out of low power mode?

Full examples:

- `[10-0120-30-14]` - 'on' message to motor
- `[10-2200-30-8b]` - 'on' response from motor

## `31` Turn off
Sent (among others) some time after setting the display to 'off' using the lower button.
Request has a single byte payload which seems to only be '00' or '01', response has no payload.
After this the motor usually sends serveral special messages, and then stops sending, or responding to messages.
Best guess so far it's a 'off' command of sorts for the motor, putting it into low power mode?
Not sure what the value 00/01 means, both seem to be used, haven't found a distinct pattern yet.
Usually soon followed by a `11` message from the motor to the BMS.

Full examples:

- `[10-0121-3100-22]` - 'off' message to motor, with value '00'
- `[10-2200-31-1a]` - 'off' response from motor

## `32` Enable assist
This message is sent by the BMS to the motor.
There is no payload in either the request or response.
It's sent usually very shortly after setting a assist mode on the display.
It's sent only if the motor has already been turned on by a 'on' command.
Best guess so far it's a 'enable assist' command of sorts for the motor?
Usually soon followed by a `12` message from the motor to the BMS with value `01`.

Full examples:

- `[10-0120-32-75]` - 'enable assist' message to motor
- `[10-2200-32-ea]` - 'enable assist' response from motor

## `33` Disable assist
This message is sent by the BMS to the motor.
There is no payload in either the request or response.
It's sent usually very shortly after setting the assist level 'off' on the display.
Quite often just before sending an 'off' command to the motor, but not always (I guess when the bike is still moving).
Best guess so far it's a 'disable assist' command of sorts for the motor?
Usually soon followed by a `12` message from the motor to the BMS with value `00`.

Full examples:

- `[10-0120-33-e4]` - 'disable assist' message to motor
- `[10-2200-33-7b]` - 'disable assist' response from motor

## `34` Set assist level
This message is sent by the BMS to the motor.
The request has a single byte payload, with value `01`,`02` or `03`. The response has no payload.
It's sent usually very shortly after setting the assist level on the display, including the initial level.
It's always sent after enabling assist with `32`, and before disabling assist with `33`.
Best guess so far it's a 'set assist' command of sorts for the motor?

Full examples:

- `[10-0121-3401-7f]` - 'set assist' message to motor with value '01'
- `[10-2200-33-7b]` - 'set assist' response from motor
