# TODO: functionality: manual override by user command
# (eg. if duration='user' then do something different)

import RPi.GPIO as GPIO
import time
import sys

# CLI: > ./zone_control.py ['zone1'] [duration]
#  zone = sys.argv[1]  # would need a dict lookup here if multiple zones were being implemented
zone = 21  # GPIO29, arbitrary choice
duration = sys.argv[2]

GPIO.setmode(GPIO.BCM)
GPIO.setup(zone, GPIO.OUT)

# script needs to take command line argument “duration” - sprinkle time in minutes

duration = int(duration) * 60  # puts duration into seconds
start_time = time.time()
GPIO.output(zone, GPIO.HIGH)
elapsed_time = time.time() - start_time
while duration > elapsed_time:
    time.sleep(1)
    elapsed_time = time.time() - start_time
GPIO.output(zone, GPIO.LOW)
sys.exit()
