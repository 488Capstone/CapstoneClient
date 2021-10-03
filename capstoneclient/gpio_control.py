# DW 2021-10-03-12:21 This file is meant to handle some of the GPIO setup
# at this point it's particularly meant to handle the gpio states at raspi initial power up
import time
import RPi.GPIO as GPIO
from capstoneclient.raspi_pins import RASPI_PIN

def state_str(boolval):
    if boolval: return "HI"
    else:       return "LO"
def state_gpio(boolval):
    if boolval: return GPIO.HIGH
    else:       return GPIO.LOW

def raspi_startup():
    pinstate = {
            "polarity":False,
            "shutdown":False,
            "ps_shutoff":False,
            "valve1_enable":False,
            "valve2_enable":False,
            "valve3_enable":False,
            "valve4_enable":False,
            "valve5_enable":False,
            "valve6_enable":False
            }
    #DW 2021-10-03-13:29 turns out there's no reason to store the old mode
    # the gpio code ONLY allows one mode...
    #prior_pinmode = GPIO.getmode()

    #DW 2021-10-03-13:30 is there any point to setting this since something
    # is already doing it in our imports? who knows... let's just keep just incase
    GPIO.setmode(GPIO.BCM)
    outputpin_names = pinstate.keys()
    for key in outputpin_names:
        value = pinstate[key]
        print(f"OUTPUT {key}:{state_str(value)}")
        pinnum = RASPI_PIN[key]
        GPIO.setup(pinnum, GPIO.OUT, initial=state_gpio(value))
    #TODO DW 2021-10-03-12:20 should we apply some default pull ups/downs to the inputs?
    for key in RASPI_PIN.keys():
        if key not in outputpin_names:
            print(f"INPUT {key}")
            pinnum = RASPI_PIN[key]
            GPIO.setup(pinnum, GPIO.IN)

    #DW 2021-10-03-13:30 no longer needed
    #GPIO.setmode(prior_pinmode)