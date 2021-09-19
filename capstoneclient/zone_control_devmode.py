#!/usr/bin/python3
# TODO: functionality: manual override by user command
# (eg. if duration='user' then do something different)

from datetime import datetime
import time
import sys

print("{}---zone_control_devmode.py:: {} {}".format(str(datetime.now()), sys.argv[1], sys.argv[2]))

# CLI: > ./zone_control.py ['zone1'] [duration]
#TODO dict lookup for zones (from db I guess)
#  zone = sys.argv[1]  # would need a dict lookup here if multiple zones were being implemented
zone = 21  # GPIO29, arbitrary choice
duration = sys.argv[2]

# script needs to take command line argument “duration” - sprinkle time in minutes
duration = int(float(duration)) # puts duration into seconds #DW for developer mode we're going to accelerate all actions. so lets make minutes==seconds
start_time = time.time()
print("{}---zone_control_devmode.py:: Zone1(pin{}) ENABLED".format(str(datetime.now()),zone))
elapsed_time = time.time() - start_time
while duration > elapsed_time:
    time.sleep(1)
    elapsed_time = time.time() - start_time

print("{}---zone_control_devmode.py:: Zone1(pin{}) DISABLED".format(str(datetime.now()),zone))
sys.exit()
