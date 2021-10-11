# DW 2021-10-03-12:21 This file is meant to handle some of the GPIO setup
# at this point it's particularly meant to handle the gpio states at raspi initial power up
#import time
import RPi.GPIO as GPIO
from capstoneclient.raspi_pins import RASPI_PIN, RASPI_OUTPUTS

#DW 2021-10-11-11:25 we don't need the cleanup on exit for now
#import atexit #DW to cleanup the gpio stuff when python3 exits

GPIO_SETUP_DONE = False

#TODO DW 2021-10-11-10:44 decision: Do we want to initialize all gpio at bootup and never again, or every time this file is called?
#   I will need to think on this for awhile. I guess for now we'll load/unload every time python is instantiated
# The recommendation by RPi is to cleanup after every script use. So we'll stick with that for now.

def state_str(val):
    if isinstance(val, bool):
        if val: return "HI"
        else:       return "LO"
    if isinstance(val, int):
        if val>0: return "HI"
        else:       return "LO"
    else:
        return "UNKNOWN"

#DW 2021-10-11-09:35 mapping function, maps True/1 to GPIO.HIGH and False/0 to GPIO.LOW
def state_gpio(val):
    if isinstance(val, bool):
        if val: return GPIO.HIGH
        else:       return GPIO.LOW
    if isinstance(val, int):
        if val>0: return GPIO.HIGH
        else:       return GPIO.LOW
    else:
        return None

def read_pin(name):
    #print(f"read_pin GPIO_SETUP_DONE {GPIO_SETUP_DONE}")
    if not GPIO_SETUP_DONE:
        setup_gpio()
    pinnum = get_pin(pin)
    if pinnum is not None:
        return GPIO.input(pinnum)

# take the pin num/name and confirm it's in our BCM pin list otherwise return None
def get_pin(pin):
    pinnum = None
    if isinstance(pin, int):
        if pin in RASPI_PIN.values():
            pinnum = pin
    elif isinstance(pin, str):
        if pin in RASPI_PIN.keys():
            pinnum = RASPI_PIN[pin]
    if pinnum is None:
        print(f"{pin} not found in {RASPI_PIN}")
    return pinnum

# name corresponds to the pin name from our pcb schematic, value is True or False
def write_pin(pin, value):
    #print(f"write_pin GPIO_SETUP_DONE {GPIO_SETUP_DONE}")
    if not GPIO_SETUP_DONE:
        setup_gpio()
    pinnum = get_pin(pin)
    pinval = state_gpio(value)
    if pinnum is not None and pinval is not None:
        return GPIO.output(pinnum, pinval)

def cleanup():
    #print(f"Cleaning up GPIO setup on Exit")
    GPIO.cleanup()

def setup_gpio(setDefaultStates=False, verbose=False):
    global GPIO_SETUP_DONE
    #print(f"setup_gpio GPIO_SETUP_DONE {GPIO_SETUP_DONE}")
    #DW only do the setup once per python session
    if not GPIO_SETUP_DONE:
        #DW 2021-10-11-08:05 'ps_shutoff' will turn off the power path from the wall adapter power supply
        #to the MPPT Vsup_in (VDC_IN/VIN), which will turn off both the 5V & 9V rails
        #'shutdown' will turn off the 9V alone
        #DW 2021-10-11-08:08 to save power, lets try enabling the 9V solenoid supply on demand
        #               So we'll turn 9V on, drive H-bridge, then turn 9V off
        pinstate = RASPI_OUTPUTS

        #DW 2021-10-03-13:29 turns out there's no reason to store the old mode
        # the gpio code ONLY allows one mode...
        #prior_pinmode = GPIO.getmode()

        #DW 2021-10-03-13:30 is there any point to setting this since something
        # is already doing it in our imports? who knows... let's just keep just incase
        GPIO.setmode(GPIO.BCM)
        outputpin_names = pinstate.keys()
        for key in outputpin_names:
            value = pinstate[key]
            if verbose:
                print(f"OUTPUT {key}:{state_str(value)}")
            pinnum = RASPI_PIN[key]
            if setDefaultStates:
                #TODO DW 2021-10-11-08:40 does initial state write that state now? Or is it just
                #   an info type variable?
                GPIO.setup(pinnum, GPIO.OUT, initial=state_gpio(value))
            else:
                GPIO.setup(pinnum, GPIO.OUT)

        #TODO DW 2021-10-03-12:20 should we apply some default pull ups/downs to the inputs?
        for key in RASPI_PIN.keys():
            if key not in outputpin_names:
                if verbose:
                    print(f"INPUT {key}")
                pinnum = RASPI_PIN[key]
                GPIO.setup(pinnum, GPIO.IN)
        GPIO_SETUP_DONE = True
        #print(f"setup_gpio end GPIO_SETUP_DONE {GPIO_SETUP_DONE}")
        #DW 2021-10-03-13:30 no longer needed
        #GPIO.setmode(prior_pinmode)

def raspi_startup():
    # run the setup gpio func and have it set the default startup state of the outputs
    setup_gpio(True, True)

#DW 2021-10-03-16:29 every time the python code runs we need to re-set up the gpio's
#DW 2021-10-11-09:05 for now, lets initialize the gpio any time this file is called
#   rather than having to call gpio_control.setup_gpio() EVERY time
#   If this becomes inefficient in the future, change it.
#DW 2021-10-11-11:24 we want the gpio outputs to remain driven, for example 'shutdown' should remain 
#   high until we want to execute a valve (on/off).
#setup_gpio(False, False)

#DW 2021-10-11-10:42 register the cleanup function to be called when we exit python session
#atexit.register(cleanup)

