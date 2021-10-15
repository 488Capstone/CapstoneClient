# DW 2021-10-14-18:50 This is my attempt to make most of our code runnable from a non-raspberry pi 
#   environment. Like my raspbian desktop virtual machine.
#   The idea is to make identical function names that mostly just print, so we can see the flow
#   of the system without actually messing with the pins

######################################################################3
# BEGIN capstoneclient.gpio_control
######################################################################3
def setmode(*args):
    pass

def setwarnings(*args):
    pass

BCM = "BCM"
BOARD = "BOARD"
HIGH = "HIGH"
LOW = "LOW"
OUT = "OUT"
IN = "IN"

def input(*args):
    print(f"GPIO.input({args})")

def output(*args):
    print(f"GPIO.output({args})")

def setup(*args):
    print(f"GPIO.setup({args})")

######################################################################3
# END capstoneclient.gpio_control
######################################################################3
######################################################################3
# BEGIN capstoneclient.sensors
######################################################################3
def read_baro_sensor(*args):
    print(f"read_baro_sensor({args})")
    return [1, 1, 1, 1]

def read_soil_sensor(*args):
    print(f"read_soil_sensor({args})")
    return 1, 1

def read_adc(*args):
    print(f"read_adc({args})")
    return 1, 1

def read_adc_for (select, verbose=True, *args):
    print(f"read_adc_for({select},{verbose},{args})")
    rtrnval = 1
    if select == 'all':
        rtrnval = {'key':1}
    return rtrnval

######################################################################3
# END capstoneclient.sensors
######################################################################3
