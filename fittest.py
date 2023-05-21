#
#
#   Simple test script to interface with a TSI PortaCount Plus, version for the German Bundeswehr
#

import serial
import io
import statistics
import time
import re
import sys
import getopt

port = "loop://"
baudrate = 1200
number = 8
#matcher="Conc.\\s*(\\d*\\.?\\d*)\\s*#"
matcher="^(\\d*\\.\\d*)"
# defaults
ff_pass_level = 100
num_exercises = 8
amb_purge_time = 4 #seconds
amb_sample_time = 5 #seconds
mask_purge_time = 11 #seconds
mask_sample_time = 40 #seconds
mode_osha_classic = True
mode_osha_modified = False

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "p:r:m:n:t",
                               ["port =",
                                "baudrate =",
                                "mode =",
                                "number =",
                                "threshold ="])

except:
    print("Error")

for opt, arg in opts:
    if opt in ['-p', '--port']:
        port = arg
    elif opt in ['-r', '--baudrate']:
        baudrate = arg
    elif opt in ['-m', '--mode']:
        mode = arg
    elif opt in ['-n', '--number']:
        number = arg
    elif opt in ['-t', '--threshold']:
        ff_pass_level = arg

ff_pass_level = 100
num_exercises = number
if mode == "classic":
    mode_osha_classic = True
    mode_osha_modified = False
    num_exercises = 8
    ff_pass_level = 100
if mode == "modified":
    mode_osha_classic = False
    mode_osha_modified = True
    ff_pass_level = 100



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
ser = serial.serial_for_url(port, timeout=1, do_not_open=True)
# PortaCount is baudrate 1200, no parity, 8 bit, 1 stopbit
# hardware flow control (CTS) is non-required per DIP switch 8 (set to ON, confusingly) in the factory config
ser.baudrate = baudrate
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE
ser.bytesize = serial.EIGHTBITS
ser.open()
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser), newline="\n")

# switch to external control mode
print("Switching PortaCount into external control mode.")
sio.write("J\r")
sio.flush()

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


        # Pre-mask ambient sample
        print("Analyzing ambient air.")
        t_end = time.monotonic() + amb_sample_time
        amb_particles_pre = 0
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


    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + mask_sample_time
    mask_particles = 0
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


    # Post-mask ambient sample
    print("Analyzing ambient air.")
    t_end = time.monotonic() + amb_sample_time
    amb_particles_post = 0
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

def ft_osha_modified():
    result = []
    print("Exercise #1 (20 sec + 30 sec + purge time)")
    # Switch to ambient inlet
    print("Switching to ambient inlet port.")
    sio.write("VN\r")
    sio.flush()

    # Ambient purge
    print("Purging.")
    time.sleep(amb_purge_time)


    # Pre-mask ambient sample
    print("Analyzing ambient air.")
    t_end = time.monotonic() + 20
    amb_particles_pre = 0
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


    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + 30
    mask_particles_1 = 0
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            mask_particles_1 = mask_particles_1 + float(x.lastgroup)

    print("Exercise #2 (30 sec)")
    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + 30
    mask_particles_2 = 0
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            mask_particles_2 = mask_particles_2 + float(x.lastgroup)

    print("Exercise #3 (30 sec)")
    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + 30
    mask_particles_3 = 0
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            mask_particles_3 = mask_particles_3 + float(x.lastgroup)

    print("Exercise #4 (30 sec + 9 sec + purge time)")
    # Mask sample
    print("Analyzing sample air.")
    t_end = time.monotonic() + 30
    line = ""
    while time.monotonic() < t_end:
        line = sio.readline()
        sio.flush()
        x = re.search(matcher,line)
        if x:
            mask_particles_4 = mask_particles_4 + float(x.lastgroup)



    # Switch to ambient inlet
    print("Switching to ambient inlet port.")
    sio.write("VN\r")
    sio.flush()

    # Ambient purge
    print("Purging.")
    time.sleep(amb_purge_time)


    # Post-mask ambient sample
    print("Analyzing ambient air.")
    t_end = time.monotonic() + 9
    amb_particles_post = 0
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

    if mask_particles_1 == 0: mask_particles_1 = 1  # prevent division by zero
    if mask_particles_2 == 0: mask_particles_2 = 1  # prevent division by zero
    if mask_particles_3 == 0: mask_particles_3 = 1  # prevent division by zero
    if mask_particles_4 == 0: mask_particles_4 = 1  # prevent division by zero

    conc_amb_pre = amb_particles_pre / (20 * 1.67)
    conc_amb_post = amb_particles_post / (9 * 1.67)
    conc_mask_1 = mask_particles_1 / (30 * 1.67)
    conc_mask_2 = mask_particles_2 / (30 * 1.67)
    conc_mask_3 = mask_particles_3 / (30 * 1.67)
    conc_mask_4 = mask_particles_4 / (30 * 1.67)

    ffactor_1 = (conc_amb_pre + conc_amb_post) / (2 * conc_mask_1)
    ffactor_2 = (conc_amb_pre + conc_amb_post) / (2 * conc_mask_2)
    ffactor_3 = (conc_amb_pre + conc_amb_post) / (2 * conc_mask_3)
    ffactor_4 = (conc_amb_pre + conc_amb_post) / (2 * conc_mask_4)
    result = [ffactor_1, ffactor_2, ffactor_3, ffactor_4]
    print("Individual fit factors")
    print(result)
    return result





ff_exercises = []

if mode_osha_modified:
    print("American CNC Modified QNFT protocol")
    ff_exercises = ft_osha_modified()
else:
    ffactor = 0
    last_amb_conc = None
    if mode_osha_classic:
        print("American CNC Classic QNFT protocol")
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
        print("Individual fit factors")
        print(ff_exercises)


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
