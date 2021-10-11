#!/usr/bin/python3

# todo: scheduler to reqs
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import sys
import schedule
from capstoneclient.raspi_pins import RASPI_PIN
import capstoneclient.gpio_control as ioc

# zone 1: GPIO19, zone 2: GPIO26, zone 3: GPIO18, zone 4: GPIO23, zone 5: GPIO24, zone 6: GPIO25
zone_lookup = (
    RASPI_PIN["valve1_enable"],
    RASPI_PIN["valve2_enable"],
    RASPI_PIN["valve3_enable"],
    RASPI_PIN["valve4_enable"],
    RASPI_PIN["valve5_enable"],
    RASPI_PIN["valve6_enable"]
    )
POLARITY = RASPI_PIN["polarity"]

def pulse_zone(zonepin):
    ENABLE_TIME = 40e-3 # seconds, needs to be fast, otherwise we just dump current like crazy
    timelimit = timedelta(seconds=ENABLE_TIME)
    start_time = datetime.now()
    ioc.write_pin(zonepin, 1)
    while ((datetime.now() - start_time) < timelimit):
        pass
    ioc.write_pin(zonepin, 0)
    now_time = datetime.now()
    total_on_dur_sec = (now_time - start_time).total_seconds()
    print(f"{now_time}---zone_control.py:: solenoid pulsed ON time = {total_on_dur_sec} sec")

def set_valve(zn, open_bool):
    channel = zone_lookup[zn-1]
    #DW 2021-10-11-09:50 need to now turn on/off the 9V supply before any zone actions
    ioc.write_pin("shutdown", 0)
    #TODO DW 2021-10-11-10:06 what happens when we're looping through all zones? 
    #   Do we really want to enable/disable the 9V supply EVERY time? consider adding
    #   feature that will just leave 9V on until all valve control is done.
    state_str = "ON"
    if open_bool:
        ioc.write_pin(POLARITY, 1)
    else:
        state_str = "OFF"
        ioc.write_pin(POLARITY, 0)

    pulse_zone(channel)
    now_time = datetime.now()
    ioc.write_pin("shutdown", 1)
    #DW clean up should come when we know we're done with the gpio.
    # I think it best to set up an atexit function for python
    #cleanup()
    print(f"{now_time}---zone_control.py:: Zone{zn}, (GPIO{channel}) {state_str}")

def open_valve(zn: int):
    set_valve(zn, True)

def open_all():
    for num in range(1,8):
        open_valve(num)

def close_valve(zn: int):
    set_valve(zn, False)
    return schedule.CancelJob

#def close_valve(zn: int):
#    channel = zone_lookup[zn - 1]
#    #GPIO.setmode(GPIO.BCM)
#    #GPIO.setup(channel, GPIO.OUT)
#    GPIO.output(channel, GPIO.LOW)
#    now_time = datetime.now()
#    print(f"{now_time}---zone_control.py:: Zone{zn}, (GPIO{channel}) OFF")
#    return schedule.CancelJob

def close_all():
    for num in range(1,8):
        close_valve(num)

def open_valve_for(zn: int, dur):
    open_valve(zn)
    schedule.every(dur).minutes.do(close_valve, zn=zn)

def cleanup():
    GPIO.cleanup()

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
            open_valve_for(zone, duration)
            while schedule.get_jobs():
                schedule.run_pending()

    else:
        print(f"bad zone/duration values: zone={zone}, duration={duration}, on_off={on_off}")

if test_mode:
    open_valve_for(1, 0.1)
    while schedule.get_jobs():
        schedule.run_pending()
    cleanup()  # cleanup turns everything to input

#sys.exit()
