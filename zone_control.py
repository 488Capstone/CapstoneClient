# TODO: either add functionality for this to function as a manual override by user command
#  (eg. if duration='user' then do something different) or need an additional script.

import RPi.GPIO as GPIO
import time
import sys

# CLI: > ./zone_control.py ['zone1'] [duration]
#  zone = sys.argv[1]  # would need a dict lookup here if multiple zones were being implemented
zone = 11  # GPIO17, arbitrary choice
duration = sys.argv[2]

GPIO.setmode(GPIO.BOARD)
GPIO.setup(zone, GPIO.OUT)

# script needs to take command line argument “duration” - sprinkle time in minutes

duration = duration * 60  # puts duration into seconds
start_time = time.time()
GPIO.output(zone, GPIO.HIGH)
elapsed_time = time.time() - start_time
while duration > elapsed_time:
    time.sleep(1)
    elapsed_time = time.time() - start_time
GPIO.output(zone, GPIO.LOW)
sys.exit()
