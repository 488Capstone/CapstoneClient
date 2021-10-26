#!/usr/bin/python3

# todo: scheduler to reqs
import time
#import RPi.GPIO as GPIO #DW 2021-10-14-18:59 all should be handled in gpio_control now just to always handle all the setup needed
from datetime import datetime, timedelta
import sys
import schedule
from capstoneclient.raspi_pins import RASPI_PIN
import capstoneclient.gpio_control as ioc
from capstoneclient.zone_control_defs import * #DW 2021-10-14-21:25 I need to import these in the webgui for manual controls

test_mode = False

#TODO DW 2021-10-11-07:55 it might be nice to have a toggle option for us during debug, if duration=0 just toggle

# todo take list of zones, durations via CLI
# for direct call to this file:
# CLI: > ./zone_control.py ['zone1'] [duration]
#DW below will turn zone1 on
# ./runPy.sh ./zone_control.py z1 0 on
#DW below will turn zone1 off
# ./runPy.sh ./zone_control.py z1 0 off
if __name__ == "__main__" and not test_mode:
    zone = int(sys.argv[1][-1])  # last char is id => check 0 to 6, 0 operates all zones
    duration = int(sys.argv[2])  # number of minutes => check 0 to 300
    on_off = sys.argv[3]

    if zone in range(7) and duration in range(301):

        if zone == 0:
            if on_off == 'on':
                open_all()
            if on_off == 'off':
                close_all()

        elif on_off == 'on' and duration == 0:
            open_valve(zone)

        elif on_off == 'off':
            close_valve(zone)
        else:
            print(f"Inside zone_control.py, zone={zone}, duration={duration}, on_off={on_off}")
            #open_valve_for(zone, duration)
            #while schedule.get_jobs():
                #schedule.run_pending()

    else:
        print(f"bad zone/duration values: zone={zone}, duration={duration}, on_off={on_off}")

#if test_mode:
#    open_valve_for(1, 0.1)
#    while schedule.get_jobs():
#        schedule.run_pending()
#    #cleanup()  # cleanup turns everything to input
#
#sys.exit()
