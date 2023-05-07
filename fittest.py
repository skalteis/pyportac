#
#
#   Simple test script to interface with a TSI PortaCount Plus, version for the German Bundeswehr
#

import serial
import io
import statistics


# defaults
ff_pass_level = 100
num_exercises = 8
amb_purge_time = 4 #seconds
amb_sample_time = 5 #seconds
mask_purge_time = 11 #seconds
mask_sample_time = 40 #seconds

# formula for particle concentrations
# conc = particles_counted / (duration * 1.67)

# formula for fit factor, first exercise
# ff = (conc_amb_presample + conc_amb_postsample) / 2 * conc_mask_sample
# To prevent division by zero:
# if conc_mask_sample = 0 then conc_mask_sample = 1 / (mask_sample_time * 1.67)
# all further exercises
# ff = (conc_amb_presample) / conc_mask_sample

# ff for all exercises combined
# fftotal = statistics.harmonic_mean(ff1, ff2, ..., ffn)

# set port, instead of loop, devicenames such as COM3 or /dev/ttyUSB0 are also supported
ser = serial.serial_for_url('loop://', timeout=1, do_not_open=True)
# PortaCount is baudrate 1200, no parity, 8 bit, 1 stopbit
# hardware flow control (CTS) is non-required per DIP switch 8 (set to ON, confusingly) in the factory config
ser.baudrate = 1200
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.bytesize = serial.EIGHTBITS
ser.open()
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), newline="\n")

sio.write(str("hello\r\n"))
sio.flush() # it is buffering. required to get the data out *now*
hello = sio.readline()
print(hello == str("hello\r\n"))
print(hello)

# switch to external control mode
sio.write("J\r")
sio.flush()

# request settings
sio.write("S\r")
sio.flush()
print(sio.readlines())

# exit external control mode
sio.write("G\r")
sio.flush()

# list of positive real valued numbers
data = [1, 3, 5, 7, 9]

# using harmonic mean function to calculate
# the harmonic mean of the given data-set
print("Harmonic Mean is % s " % (statistics.harmonic_mean(data)))