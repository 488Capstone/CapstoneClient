#!/usr/bin/python

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c)
# you can specify an I2C adress instead of the default 0x48
ads = ADS.ADS1115(i2c, address=0x48)

# Create single-ended input on channel 0
chan1 = AnalogIn(ads, ADS.P0)
chan2 = AnalogIn(ads, ADS.P1)
chan3 = AnalogIn(ads, ADS.P2)
chan4 = AnalogIn(ads, ADS.P3)


# Create differential input between channel 0 and 1
# chan = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format("raw", "v"))

while True:
    print("ch1")
    print("{:>5}\t{:>5.3f}".format(chan1.value, chan1.voltage))
    time.sleep(0.5)
    print("ch2")
    print("{:>5}\t{:>5.3f}".format(chan2.value, chan2.voltage))
    time.sleep(0.5)
    print("ch3")
    print("{:>5}\t{:>5.3f}".format(chan3.value, chan3.voltage))
    time.sleep(0.5)
    print("ch4")
    print("{:>5}\t{:>5.3f}".format(chan4.value, chan4.voltage))
    time.sleep(0.5)