import time
import RPi.GPIO as GPIO

GPIO.setup(21, GPIO.OUT)

# TODO: add user interrupt to manual control.
def manual_control():
    GPIO.output(21, GPIO.HIGH)
    print("Zone 1 is now on.")
    time.sleep(5)
    GPIO.output(21, GPIO.LOW)
    print("Zone 1 is now off.")


