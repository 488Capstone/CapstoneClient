# Top level
# This is the primary python script which will incorporate all functionality.
on_raspi = True

from crontab import CronTab
from etcalc import *
import sqlite as sl
from publish import *

try:
    from raspispecific.py import *
except:
    print('code not executing from raspi, functionality may be incomplete')
    on_raspi = False

class System:
    def __init__(self):
        self.zipcode = 12345
        self.soiltype = ' '
        self.city = ' '
        self.state = ' '

    class Zone:
        def __init__(self):
            self.applicationrate = 1.5  # inches per hour.
            self.planttype = " "  # warm grass, cool grass, flowers, shrubs.
            self.microclimate = " "  # always sunny or always shady.
            self.slope = 0  # zero slope.
            self.watering_days = []
            self.pref_time_hrs = 9 # prototype assumption; recommendation should be made based on daily temps with user approval
            self.pref_time_min = 00 # prototype assumption; recommendation should be made based on daily temps with user approval
            self.refET = 0.2 # baseline assumption until updated by startup
            self.session_time = 0

        def water_algo(self):
            emitterefficiency = {
                "rotary": 0.7
            }
            cropcoef = {
                "cool grass": 1,
                "warm grass": 1,
                "shrubs": 1,
                "flowers": 1
            }
            effectiveapplicationrate = self.applicationrate * emitterefficiency["rotary"] # assumption made for prototype.
            cropET = self.refET * cropcoef[self.planttype]
            req_watering_time = (cropET / effectiveapplicationrate) * 60 # number of minutes system will be on
            session_time = req_watering_time / len(self.watering_days) # number of minutes per session
            # since slope is assumed to be zero, every watering session will be continuous.
            plan = Schedule(zone='zone1', duration=session_time, day=self.watering_days, hour=self.pref_time_hrs, minute=self.pref_time_min)
            Schedule.water_scheduler(plan)
            return session_time


class Schedule:
    def __init__(self, zone, duration, day, hour, minute):
        self.zone = zone                                                                    # string - always 'zone1' for now
        self.duration = duration                                                            # in minutes
        self.day = day                                                                      # 0=SUN, 6=SAT
        self.hour = hour                                                                    # 0-23
        self.minute = minute                                                                # 0-59

    def water_scheduler(self):
        schedule = CronTab(user=True)                                                       # opens the crontab (list of all tasks)
        command_string = './zone_control.py ' + self.zone + ' ' + str(self.duration)        # adds appropriate args to zone_control.py
        task = schedule.new(command=command_string, comment='ZoneControl')                  # creates a new entry in the crontab
        #TODO: fix scheduling for multiple days
        for x in range(len(self.day)):
            task.dow.on(self.day[x])                                                        # day of week as per object passed to the method
            task.minute.on(self.minute)                                                     # minute-hand as per object passed to the method
            task.hour.on(self.hour)                                                         # hour-hand as per object passed to the method
            schedule.write()                                                                # finalizes the task in the crontab
        print("all tasks created")
        input("Press any key to continue.")


    def clear_tasks(self):
        schedule = CronTab(user=True)
        schedule.remove_all(comment='ZoneControl')


def op_menu():
    print("Menu:")
    print("1. My System [coming soon]")
    print("2. My Schedule [coming soon]")
    print("3. Application Rate Calibration [coming soon]")
    choice = input("Choose wisely. ")
    if choice == '1':
        my_system()
    elif choice == '2':
        print("Watering days: ",system.zone1.watering_days)
        print("Session length: ",system.zone1.session_time, "minutes per watering session")
        print("Watering time: ",system.zone1.pref_time_hrs, system.zone1.pref_time_min)
        input("Press any key to continue.")
        op_menu()
    elif choice == '3':
        pass
    else:
        print('Try again, turd')
        op_menu()


def my_system():
    print("System Data:")
    print("Location: ", system.city, system.state, system.zipcode)
    print("Yard info: ",system.zone1.soiltype, "with", system.zone1.planttype)
    print("Watering days: ",system.zone1.watering_days)
    input("Press any key to continue.")
    op_menu()


def startup():
    print('Excellent choice, sir. Startup protocol initiated.')

    # system.city = get('https://ipapi.co/city').text
    # system.state = get('https://ipapi.co/region_code').text
    # system.zipcode = get('https://ipapi.co/postal').text
    system.city = "Gulf Breeze"
    system.state = "FL"
    system.zipcode = "32563"
    print('We think you\'re in ',system.city, ',',system.state, ',', system.zipcode)
    print('For now, we\'ll assume that\'s all true.')

    system.zone1.soiltype = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or 'loamy']")
    # TODO: improve user selection of watering days
    if system.zone1.soiltype == 'sandy':
        print("Your sandy soil won't hold water well; more frequent applications of water are best to keep your plants healthy.")
        print("We recommend watering your lawn frequently - three days a week should do nicely.")
        print("We'll make it easy and say Mon-Weds-Fri for now.") # placeholder for user selection
        system.zone1.watering_days = [1,3,5]
    elif system.zone1.soiltype == 'loamy':
        print("Your loamy soil will hold water well. We recommend picking one watering day a week.")
        print("We'll make it easy and pick Wednesday for now.") # placeholder for user selection
        system.zone1.watering_days = "'WED'"
    system.zone1.planttype = input("What is the predominant plant type in this zone? [limit answers to 'cool grass', 'warm grass', 'shrubs', or 'flowers']")
    print("Okay, it looks like we have everything we need to calculate your water needs. We'll do that now.")
    system.zone1.refET = et_calculations_testing()
    print("Beep...Bop...Boop...")
    print("...")
    print("Okay! It looks like this zone will lose about", system.zone1.refET, "inches of water per day to evaporation and plant transpiration. Now we're getting somewhere!")
    system.zone1.applicationrate = 1.5
    system.zone1.session_time = System.Zone.water_algo(system.zone1)
    op_menu()


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
    # TODO: application rate calibrations
    print("2: Application rate calibration [coming soon]")
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