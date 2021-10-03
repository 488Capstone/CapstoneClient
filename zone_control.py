#!/usr/bin/python3

# todo: scheduler to reqs
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
import sys
import schedule
from capstoneclient.raspi_pins import RASPI_PIN

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
    GPIO.output(zonepin, GPIO.HIGH)
    while ((datetime.now() - start_time) < timelimit):
        pass
    GPIO.output(zonepin, GPIO.LOW)

def set_valve(zn, open_bool):
    channel = zone_lookup[zn-1]
    if open_bool:
        GPIO.outpu(POLARITY, GPIO.HIGH)
    else:
        GPIO.outpu(POLARITY, GPIO.LOW)

    pulse_zone(channel)
    now_time = datetime.now()
    print(f"{now_time}---zone_control.py:: Zone{zn}, (GPIO{channel}) ON")

def open_valve(zn: int):
    set_valve(zn, True)


def open_all():
    #GPIO.setmode(GPIO.BCM)
    for num in range(6):
        channel = zone_lookup[num]
        #GPIO.setup(channel, GPIO.OUT)
        GPIO.output(channel, GPIO.HIGH)
        now_time = datetime.now()
        print(f"{now_time}---zone_control.py:: Zone{num+1}, (GPIO{channel}) ON")


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
    #GPIO.setmode(GPIO.BCM)
    for num in range(6):
        channel = zone_lookup[num]
        #GPIO.setup(channel, GPIO.OUT)
        GPIO.output(channel, GPIO.LOW)
        now_time = datetime.now()
        print(f"{now_time}---zone_control.py:: Zone{num+1}, (GPIO{channel}) OFF")

def open_valve_for(zn: int, dur):
    open_valve(zn)
    schedule.every(dur).minutes.do(close_valve, zn=zn)


def cleanup():
    GPIO.cleanup()


test_mode = False


# todo take list of zones, durations via CLI
# for direct call to this file:
# CLI: > ./zone_control.py ['zone1'] [duration]
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

 sys.exit()
