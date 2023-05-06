#
#
#   Simple test script to interface with a TSI PortaCount Plus, version for the German Bundeswehr
#

import serial
import io
ser = serial.serial_for_url('loop://', timeout=1)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

sio.write(unicode("hello\n"))
sio.flush() # it is buffering. required to get the data out *now*
hello = sio.readline()
print(hello == unicode("hello\n"))
