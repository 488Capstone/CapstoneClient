# Top level
# This is the primary python script which will incorporate all functionality.

import datetime
import sys
from crontab import CronTab
from requests import get

on_raspi = True

try:
    from raspispecific.py import *
except:
    print('code not executing from raspi, functionality may be incomplete')
    on_raspi = False

class System:
    def __init__(self):
        zipcode = 12345
        soiltype = ' '
        city = ' '
        state = ' '
        # Assumption: system connected to water main (30 psi), each zone is 5 rotor-style sprinkler heads.

    class Zone:
        def __init__(self):
            applicationrate = 1.5  # inches per hour.
            planttype = " "  # warm grass, cool grass, flowers, shrubs.
            microclimate = " "  # always sunny or always shady.
            slope = 0  # zero slope.

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


class Schedule:
    class Job:
        def __init__(self, zone, duration, day, hour, minute):
            self.zone = zone                                     # string - always 'zone1' for now
            self.duration = duration                             # in minutes
            self.day = day                                       # Three-letter string, all caps
            self.hour = hour                                     # 0-23
            self.minute = minute                                 # 0-59

    def water_scheduler(self, job):
        schedule = CronTab(user=True)                                               # opens the crontab (list of all tasks)
        command_string = './zone_control.py ' + job.zone + ' ' + str(job.duration)  # adds appropriate args to zone_control.py
        task = schedule.new(command=command_string, comment='ZoneControl')          # creates a new entry in the crontab
        task.dow.on(job.day)                                                        # day of week as per object passed to the method
        task.minute.on(job.minute)                                                  # minute-hand as per object passed to the method
        task.hour.on(job.hour)                                                      # hour-hand as per object passed to the method
        task.write()                                                                # finalizes the task in the crontab                  # This


    def clear_tasks(self):
        schedule = CronTab(user=True)
        schedule.remove_all(comment='ZoneControl')


def startup():
    print('Excellent choice, sir. Startup protocol initiated.')
    system.city = get('https://ipapi.co/city').text
    system.state = get('https://ipapi.co/region_code').text
    system.zipcode = get('https://ipapi.co/postal').text
    print('We think you\'re in ',system.city, ',',system.state, ',', system.zipcode)
    print('For now, we\'ll assume that\'s all true.')
    system.zone1.soiltype = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or 'loamy']")
    system.zone1.planttype = input("What is the predominant type of plants in this zone? [limit answers to 'cool grass', 'warm grass', 'shrubs', or 'flowers']")


def raspi_testing():
    schedule = Schedule()
    sense = Sensors()
    baro_data = sense.baro()
    soil_data = sense.soil()
    sensor_data = [datetime.datetime.now(), baro_data[1], baro_data[2], soil_data]

    print("Welcome aboard, matey.")
    print("Menu:")
    print("1: Check sensor readings.")
    print("2: Manual zone control.")
    print("3: First startup simulation")
    choice = input("Choose wisely. ")

    if (choice == '1'):
        print("Sensor data:")
        print("Timestamp: ", sensor_data[0])
        print("Temperature: ", sensor_data[1])
        print("Barometric pressure: ", sensor_data[2])
        print("Soil moisture: ", sensor_data[3])
    elif (choice == '2'):
        System.Zone.manual_control()
    elif (choice == '3'):
        startup()
    else:
        print("You have chosen...poorly.")
        sys.exit()


def testing():
    print("Welcome aboard, matey. What'll it be?")
    print("1: First startup simulation")
    print("2: Application rate calibration [coming soon]") # TODO: application rate calibrations
    print("3: ")
    choice = input("Choose wisely. ")
    if choice == '1':
        startup()
    else:
        print('You have chosen...poorly.')
        sys.exit()


# It begins.
system = System()
system.zone1 = System.Zone()
if on_raspi == True:
    raspi_testing()
else:
    testing()