This software must *not* be used for any fit testing, does *not* comply with any relevant regulations
or standards and is meant for purely educational and research use ONLY.
Currently everything here is untested and likely does not work at all. WIP.

Usage:

    fittest.py
   
    --port COM<n> on Windows, /dev/ttyUSB<n> on Linux

    --baudrate speed in baud (default is 1200)

    --mode classic (default), modified or live

        "classic" is a 8 exercises protocol common in the US
        --number (default is 8) can be used to modify number of exercises
        By default, number 6 is skipped for calculation of the total score
        
        "modified" is a shortened four exercise version
    
        --threshold sets the overall factor needed to pass
    
        "live" is continuously outputting live factor once per second  
        with one minute interval ambient reference sampling