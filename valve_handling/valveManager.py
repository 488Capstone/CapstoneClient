#!/usr/bin/python3

import RPi.GPIO as GPIO

zone1pwr = 7
sensepwr = 29
bme280pwr = 31

GPIO.setmode(BOARD) # tells GPIO which pin identifier names to use
GPIO.setup(zone1pwr, GPIO.OUT) # pin for zone 1 control is output
GPIO.setup(sensepwr, GPIO.OUT) # pin for bme280 power control is output
GPIO.setup(bme280pwr, GPIO.OUT) # pin for soil sensor power control is output



# switching code examples:
# GPIO.output(channel, GPIO.HIGH)
# GPIO.output(channel, GPIO.LOW)