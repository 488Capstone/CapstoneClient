# todo: scheduler to reqs
import time
#import RPi.GPIO as GPIO #DW 2021-10-14-18:59 all should be handled in gpio_control now just to always handle all the setup needed
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
    #DW 2021-10-11-10:22 the zone enables are no longer working. Maybe not enough
    # time to pull up the 9V supple? Let's try waiting a little
    time.sleep(1)
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

def toggle_valve(zn: int):
    set_valve(zn, (not (bool(ioc.read_pin(POLARITY) or True))))

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
    #DW 2021-10-11-11:29 we don't want the outputs to be floating. So no cleanups for now.
    #GPIO.cleanup()
    pass

test_mode = False
