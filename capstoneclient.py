# Top level
# This is the primary python script which will incorporate all functionality.

import time
import smbus
import busio
import datetime
import sys
import RPi.GPIO as GPIO
from board import SCL, SDA
from adafruit_seesaw.seesaw import Seesaw
from crontab import CronTab


GPIO.setup(21, GPIO.OUT)

class System:
    def __init__(self, zipcode, season, soiltype, system_psi):
        self.zipcode = zipcode
        self.season = season
        self.soiltype = soiltype
        self.system_psi = system_psi
        # Assumption: system connected to water main (30 psi), each zone is 5 rotor-style sprinkler heads.

    class Zone:
        def __init__(self, applicationrate, soiltype, planttype, microclimate, slope):
            self.applicationrate = applicationrate # 1.5 inches per hour.
            self.soiltype = soiltype # only loamy or sandy.
            self.planttype = planttype # warm grass, cool grass, flowers, shrubs.
            self.microclimate = microclimate # sunny or shady.
            self.slope = slope # zero slope.

        def manual_control(self): # TODO: add user interrupt to manual control.
            GPIO.output(21, GPIO.HIGH)
            print("Zone 1 is now on.")
            time.sleep(5)
            GPIO.output(21, GPIO.LOW)
            print("Zone 1 is now off.")


        def water_algo(self, zone): # TODO: Watering algorithm.

            plantreqs = { # inches of water per week. All this data is based on a quick google for rough-draft purposes.
                "warm grass": 1,
                "cool grass": 2,
                "flowers": 0.7,
                "shrubs": 1
            }

            emitterefficiency = {
                "rotary": 0.7
            }

            plantwaterreq = plantreqs[plantType]  # Inches of water the plants need per week
            wateringefficiency = emitterefficiency["rotary"] # assumption made for prototype.

            # Amount of water evaporating per week:
            # This will probably need to be calculated outside of this function
            # Will probably take into account humidity, ambient temperature, soil type, microclimate, plant type...

            # Amount of water that needs to be applied per week:
            zoneTotalWaterReq = plantWaterReq + predictedETRate

            # Amount of time this zone should be "on" in minutes:

            # Number of weekly waterings:

            # How long should each watering session last?

            # Should each watering session be continuous or include "soak in" breaks?

            avgpreciprate = 1.5  # inches per hour; this is a prototyping simplification. this rate will need to be calculated based on line pressure, number of emitters on the line, and nozzle diameter of the specified emitter.


        #  def et_calculations(self,): # TODO: Calculate evapotranspiration


class Sensors():


    def baro(self):
        bus = smbus.SMBus(1)  # BME280 address, 0x76(118)
        # Read data back from 0x88(136), 24 bytes
        b1 = bus.read_i2c_block_data(0x77, 0x88, 24)  # Convert the data

        # Temp coefficients
        dig_T1 = b1[1] * 256 + b1[0]
        dig_T2 = b1[3] * 256 + b1[2]
        if dig_T2 > 32767:
            dig_T2 -= 65536
        dig_T3 = b1[5] * 256 + b1[4]
        if dig_T3 > 32767:
            dig_T3 -= 65536
        # Pressure coefficients
        dig_P1 = b1[7] * 256 + b1[6]
        dig_P2 = b1[9] * 256 + b1[8]
        if dig_P2 > 32767:
            dig_P2 -= 65536
        dig_P3 = b1[11] * 256 + b1[10]
        if dig_P3 > 32767:
            dig_P3 -= 65536
        dig_P4 = b1[13] * 256 + b1[12]
        if dig_P4 > 32767:
            dig_P4 -= 65536
        dig_P5 = b1[15] * 256 + b1[14]
        if dig_P5 > 32767:
            dig_P5 -= 65536
        dig_P6 = b1[17] * 256 + b1[16]
        if dig_P6 > 32767:
            dig_P6 -= 65536
        dig_P7 = b1[19] * 256 + b1[18]
        if dig_P7 > 32767:
            dig_P7 -= 65536
        dig_P8 = b1[21] * 256 + b1[20]
        if dig_P8 > 32767:
            dig_P8 -= 65536
        dig_P9 = b1[23] * 256 + b1[22]
        if dig_P9 > 32767:
            dig_P9 -= 65536  # BME280 address, 0x77
        # Read data back from 0xA1(161), 1 byte
        dig_H1 = bus.read_byte_data(0x77, 0xA1)  # BME280 address, 0x76
        # Read data back from 0xE1(225), 7 bytes
        b1 = bus.read_i2c_block_data(0x77, 0xE1, 7)  # Convert the data

        # Humidity coefficients
        dig_H2 = b1[1] * 256 + b1[0]
        if dig_H2 > 32767:
            dig_H2 -= 65536
        dig_H3 = (b1[2] & 0xFF)
        dig_H4 = (b1[3] * 16) + (b1[4] & 0xF)
        if dig_H4 > 32767:
            dig_H4 -= 65536
        dig_H5 = (b1[4] / 16) + (b1[5] * 16)
        if dig_H5 > 32767:
            dig_H5 -= 65536
        dig_H6 = b1[6]
        if dig_H6 > 127:
            dig_H6 -= 256  # BME280 address, 0x76(118)

        # Select control humidity register, 0xF2(242)
        #		0x01(01)	Humidity Oversampling = 1
        bus.write_byte_data(0x77, 0xF2, 0x01)

        # Select Control measurement register, 0xF4(244)
        #		0x27(39)	Pressure and Temperature Oversampling rate = 1
        #					Normal mode
        bus.write_byte_data(0x77, 0xF4, 0x27)
        # BME280 address, 0x76(118)
        # Select Configuration register, 0xF5(245)
        #		0xA0(00)	Stand_by time = 1000 ms
        bus.write_byte_data(0x77, 0xF5, 0xA0)
        time.sleep(0.5)  # BME280 address, 0x76(118)
        # Read data back from 0xF7(247), 8 bytes
        # Pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB
        # Temperature xLSB, Humidity MSB, Humidity LSB
        data = bus.read_i2c_block_data(0x77, 0xF7, 8)

        # Convert pressure and temperature data to 19-bits
        adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
        adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16  # Convert the humidity data
        adc_h = data[6] * 256 + data[7]

        # Temperature offset calculations
        var1 = (adc_t / 16384.0 - dig_T1 / 1024.0) * dig_T2
        var2 = ((adc_t / 131072.0 - dig_T1 / 8192.0) * (adc_t / 131072.0 - dig_T1 / 8192.0)) * dig_T3
        t_fine = (var1 + var2)
        cTemp = (var1 + var2) / 5120.0
        fTemp = cTemp * 1.8 + 32

        # Pressure offset calculations
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * dig_P6 / 32768.0
        var2 = var2 + var1 * dig_P5 * 2.0
        var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
        var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_P1
        p = 1048576.0 - adc_p
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = dig_P9 * p * p / 2147483648.0
        var2 = p * dig_P8 / 32768.0
        pressure = (p + (var1 + var2 + dig_P7) / 16.0) / 100

        # Humidity offset calculations
        var_H = (t_fine - 76800.0)
        var_H = (adc_h - (dig_H4 * 64.0 + dig_H5 / 16384.0 * var_H)) * (
                    dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * var_H * (1.0 + dig_H3 / 67108864.0 * var_H)))
        humidity = var_H * (1.0 - dig_H1 * var_H / 524288.0)
        if humidity > 100.0:
            humidity = 100.0
        elif humidity < 0.0:
            humidity = 0.0

        # packages everything up all nice and neat, returns as an array.
        data = [cTemp, fTemp, pressure, humidity]
        return data

    def soil(self):
        touch = Seesaw(busio.I2C(SCL, SDA), addr=0x36).moisture_read()
        return touch

    #  def adc(self, zone): # TODO: Read ADC.


class Schedule:
    class Job:
        def __init__(self, zone, duration, day, hour, minute):
            self.zone = zone                                                               # string - always 'zone1' for now
            self.duration = duration                                                       # in minutes
            self.day = day                                                                 # Three-letter string, all caps
            self.hour = hour                                                               # 0-23
            self.minute = minute                                                           # 0-59

    def water_scheduler(self, job):
        schedule = CronTab(user=True)                                                      # opens the crontab (list of all tasks)
        command_string = './zone_control.py ' + job.zone + ' ' + str(job.duration)         # adds appropriate args to zone_control.py
        task = schedule.new(command=command_string, comment='ZoneControl')                 # creates a new entry in the crontab
        task.dow.on(job.day)                                                               # day of week as per object passed to the method
        task.minute.on(job.minute)                                                         # minute-hand as per object passed to the method
        task.hour.on(job.hour)                                                             # hour-hand as per object passed to the method
        task.write()                                                                       # finalizes the task in the crontab                  # This


    def clear_tasks(self):
        schedule = CronTab(user=True)
        schedule.remove_all(comment='ZoneControl')


def testing():
    schedule = Schedule()
    sense = Sensors()
    baro_data = sense.baro()
    soil_data = sense.soil()
    sensor_data = [datetime.datetime.now(), baro_data[1], baro_data[2], soil_data]

    print("Welcome aboard, matey.")
    print("Menu:")
    print("1: Check sensor readings.")
    print("2: Manual zone control.")
    print("3: ")
    choice = input("Choose wisely. ")

    if (choice == '1'):
        print("Sensor data:")
        print("Timestamp: ", sensor_data[0])
        print("Temperature: ", sensor_data[1])
        print("Barometric pressure: ", sensor_data[2])
        print("Soil moisture: ", sensor_data[3])
    elif (choice == '2'):
        System.Zone.manual_control()
    else:
        print("You have chosen...poorly.")
        sys.exit()

testing()
