#
#
#   Simple test script to interface with a TSI PortaCount Plus, version for the German Bundeswehr
#

import serial
import io
import statistics
import time
import re

# defaults
#ff_pass_level = 100
#num_exercises = 8
#amb_purge_time = 4 #seconds
#amb_sample_time = 5 #seconds
#mask_purge_time = 11 #seconds
#mask_sample_time = 40 #seconds
#mode_osha_classic = True
#mode_osha_modified = False

# defaults
ff_pass_level = 100
num_exercises = 8
amb_purge_time = 1 #seconds
amb_sample_time = 1 #seconds
mask_purge_time = 1 #seconds
mask_sample_time = 1 #seconds
mode_osha_classic = True
mode_osha_modified = False


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

#sio.write(str("hello\r\n"))
#sio.flush() # it is buffering. required to get the data out *now*
#hello = sio.readline()
#print(hello == str("hello\r\n"))
#print(hello)

# switch to external control mode
print("Switching PortaCount into external control mode.")
sio.write("J\r")
sio.flush()

# request settings
sio.write("S\r")
sio.flush()
print(sio.readlines())

print("Starting fit test.")


def ft_exercise(last_amb_conc=None, presample_ambient=False):
    result = []
    if presample_ambient:
        # Switch to ambient inlet
        print("Switching to ambient inlet port.")
        sio.write("VN\r")
        sio.flush()

        # Ambient purge
        print("Purging.")
        time.sleep(amb_purge_time)
        #t_end = time.monotonic() + amb_purge_time
        #while time.monotonic() < t_end:
        #    # do whatever you do

        # Pre-mask ambient sample
        print("Analyzing ambient air.")
        t_end = time.monotonic() + amb_sample_time
        amb_particles_pre = 0
        matcher="Conc.\\s*(\\d*\\.?\\d*)\\s*#"
        line = ""
        while time.monotonic() < t_end:
            line = sio.readline()
            sio.flush()
            x = re.search(matcher,line)
            if x:
                amb_particles_pre = amb_particles_pre + float(x.lastgroup)


    # Switch to mask inlet
    print("Switching to sample inlet port.")
    sio.write("VF\r")
    sio.flush()

    # Mask purge
    print("Purging.")
    time.sleep(mask_purge_time)
    #t_end = time.monotonic() + mask_purge_time
    #while time.monotonic() < t_end:
    #    # do whatever you do

    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + mask_sample_time
    mask_particles = 0
    matcher = "Conc.\\s*(\\d*\\.?\\d*)\\s*#"
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            mask_particles = mask_particles + float(x.lastgroup)



    # Switch to ambient inlet
    print("Switching to ambient inlet port.")
    sio.write("VN\r")
    sio.flush()

    # Ambient purge
    print("Purging.")
    time.sleep(amb_purge_time)
    #t_end = time.monotonic() + amb_purge_time
    #while time.monotonic() < t_end:
    #    # do whatever you do

    # Post-mask ambient sample
    print("Analyzing ambient air.")
    t_end = time.monotonic() + amb_sample_time
    amb_particles_post = 0
    matcher="Conc.\\s*(\\d*\\.?\\d*)\\s*#"
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            amb_particles_post = amb_particles_post + float(x.lastgroup)

    # Switch to mask inlet
    print("Switching to sample inlet port.")
    sio.write("VF\r")
    sio.flush()

    #
    # Calculate fit factor
    #

    if (mask_particles == 0): mask_particles = 1  # prevent division by zero

    conc_amb_post = amb_particles_post / (amb_sample_time * 1.67)
    conc_mask = mask_particles / (mask_sample_time * 1.67)


    if presample_ambient:
        conc_amb_pre = amb_particles_pre / (amb_sample_time * 1.67)
        ffactor = (conc_amb_pre + conc_amb_post) / (2 * conc_mask)
        result = [ffactor, conc_amb_post]
    else:
        ffactor = (last_amb_conc + conc_amb_post) / (2 * conc_mask)
        result = [ffactor, conc_amb_post]
    return result


ff_exercises = []
ffactor = 0
last_amb_conc = None
for i in range(num_exercises):
    print("Exercise # "+ str(i + 1) + " of " + str(num_exercises) + "...")
    if i == 0:
        ffactor = ft_exercise(last_amb_conc=last_amb_conc, presample_ambient=True)
        last_amb_conc = ffactor[1]
    else:
        ffactor = ft_exercise(last_amb_conc=last_amb_conc, presample_ambient=False)
    if mode_osha_classic and i == 5:
        print("Fit factor: " + str(ffactor[0]) + " IGNORED! (grimace exercise)")
    else:
        print("Fit factor: " + str(ffactor[0]))
    ff_exercises.append(ffactor[0])

if mode_osha_classic:
    ff_exercises.pop(5)

overall_ff = statistics.harmonic_mean(ff_exercises)
print("===========")
print("OVERALL FIT FACTOR: " + str(overall_ff))
print("FIT FACTOR THRESHOLD: " + str(ff_pass_level))
if (overall_ff > ff_pass_level):
    print("PASSED FIT TEST.")
else:
    print("FAILED FIT TEST!")


# exit external control mode
sio.write("G\r")
sio.flush()

# list of positive real valued numbers
#data = [1, 3, 5, 7, 9]

# using harmonic mean function to calculate
# the harmonic mean of the given data-set
#print("Harmonic Mean is % s " % (statistics.harmonic_mean(data)))