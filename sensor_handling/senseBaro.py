# Above: senseManager.py

# When called, this module polls the BME280 sensor for all data.

# BME280 uses I2C interface to provide temp, pressure, humidity.

# I2C address is 0x76 or 0x77

# Pinout:
    # VCC --> 3.3V
    # GND --> GND
    # SCL --> SCL
    # SDA --> SDA
    
import bme280
import smbus2
from time import sleep

port = 1
address = 0x77 # Adafruit BME280 address. Other BME280s may be different
bus = smbus2.SMBus(port)

bme280.load_calibration_params(bus,address)

# uncomment this section to test everything in the command prompt.
# while True:
#    bme280_data = bme280.sample(bus,address)
#    humidity  = bme280_data.humidity
#    pressure  = bme280_data.pressure
#    ambient_temperature = bme280_data.temperature
#    print(humidity, pressure, ambient_temperature)
#    sleep(1)
    
def read_all():
    bme280_data = bme.sample(bus,address)
    return bme280_data.humidity, bme280_data.pressure, bme280_data.temperature