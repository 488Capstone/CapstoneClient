# DW 2021-10-14-18:50 This is my attempt to make most of our code runnable from a non-raspberry pi 
#   environment. Like my raspbian desktop virtual machine.
#   The idea is to make identical function names that mostly just print, so we can see the flow
#   of the system without actually messing with the pins

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

