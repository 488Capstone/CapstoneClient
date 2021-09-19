#####################################################################
# Title: capstoneclient.py                                          #
# Authors: Collin T, Doug W, Nolan B, Xavier R, Jeff M              #
# this script contains setup and operation of the device.           #
#####################################################################

import os
import sys
import requests
from crontab import CronTab
from cron_descriptor import get_description
import datetime
from dailyactions import gethistoricaldata, water_algo, ZONE_CONTROL_COMMENT_NAME, LOG_FILE_NAME
from db_manager import DBManager
from models import SystemZoneConfig

DWDBG = False

# todo: maybe environment variable
# controls imports that only work on raspberry pi. This allows code to stay functional for development on other systems.
on_raspi = True
try:
    from raspispecific import *
except:
    input("not on raspi; functionality will be incomplete. Press enter to acknowledge.")
    on_raspi = False
    DWDBG = True


# op_menu() is the landing spot for operations.
def op_menu():
    # TODO: create water budget functionality
    # TODO: allow for WaterSense prescribed watering day schedules
    print("Menu:")
    print("1. My System")
    print("2. My Schedule")
    print("3. Application Rate Calibration")
    print("4. Settings [coming soon]")
    print("5. Water budgeting [coming soon]")
    print("0. Exit")
    choice = input("Choose wisely. ")
    if choice == '0': 
        print("Exiting program")
        exit()
    if choice == '1': my_system()
    elif choice == '2': my_schedule()
    elif choice == '3': application_rate_cal()
    elif choice == '4' or '5':
        print("What is exactly do you think, \"coming soon\" means...?")
        op_menu()
    else:
        print('Try again, turd')
        op_menu()


# my_system() displays basic system/zone data when requested from op_menu()
# todo: these not returning config just set up
def my_system():


    print("System Data:")
    print(f"Location: {my_sys.city}, {my_sys.state}, {my_sys.zipcode}")
    print(f"Zone 1 soil is primarily {zone1.soil_type}. "
          f"Application rate is {zone1.application_rate} inches per hour.")
    input("Press any key to continue.")
    op_menu()


# my_schedule() displays basic scheduling data when requested from op_menu()
def my_schedule():
    # TECHNICAL DEBT! This code is not hardened against all possible inputs.
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    days = [] # init empty array

    # dump every ZoneControl task into days array:
    for tasks in schedule:
        if tasks.comment == ZONE_CONTROL_COMMENT_NAME:
            days.append([str(tasks[4]), str(tasks[0]), str(tasks[1]), str(tasks.command[23:26])])                      #
                                                                                                                       #
    # parse days array into usable strings:
    day_string = ""
    for x in range(len(days)):
        if days[x][0] == "MON": days[x][0] = "Monday"
        elif days[x][0] == "TUE": days[x][0] = "Tuesday"
        elif days[x][0] == "WED": days[x][0] = "Wednesday"
        elif days[x][0] == "THU": days[x][0] = "Thursday"
        elif days[x][0] == "FRI": days[x][0] = "Friday"
        elif days[x][0] == "SAT": days[x][0] = "Saturday"
        elif days[x][0] == "SUN": days[x][0] = "Sunday"

        if days[x][1] == "0": days[x][1] = "00"

        if int(days[x][2]) < 12: days[x][1] = days[x][1] + "AM"
        else: days[x][1] = days[x][1] + "PM"

        if x+1 == len(days):
            day_string = day_string + "and " + days[x][0]
        else:
            day_string = day_string + days[x][0] + ", "
    print("Zone 1 is currently scheduled to run on {}." .format(day_string))
    for x in range(len(days)):
        print("On {}, zone 1 will run for {} minutes starting at {}:{}." \
              .format(days[x][0], days[x][3], days[x][2], days[x][1]))
    op_menu()


def startup():

    print('Excellent choice, sir. Startup protocol initiated.')

    # Get location data from IP address:
    loc = requests.get('http://ipapi.co/json/?key=H02y7T8oxOo7CwMHhxvGDOP7JJqXArMPjdvMQ6XhA6X4aR4Tub').json()

    # enter location into system database:
    my_sys.city, my_sys.state, my_sys.zipcode, my_sys.lat, my_sys.long = \
        loc['city'], loc['region_code'], loc['postal'], loc['latitude'], loc['longitude']

    db.add(my_sys)  # add/update object

    print(f"We think you're in {my_sys.city}, {my_sys.state} {my_sys.zipcode}")
    print(f"Lat/long: {my_sys.lat}, {my_sys.long}")
    print("For now, we'll assume that's all true.")

    # get historical weather / solar data, build database.
    # This does the past week as a starting point for a water deficit.
    history_items_list = gethistoricaldata(days=7, latitude=my_sys.lat, longitude=my_sys.long)
    print("Database of historical environmental data built.")

    # build system info:
    print("Lets talk about Zone 1, since this is a limited prototype and all.")
    soil_type = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or ""'loamy']")
    while soil_type != ("sandy" or "loamy"):
        soil_type = input("Sorry, we didn't quite catch that...is the predominant soil type in this zone sandy or loamy?")

    zone1.soil_type = soil_type


    # TECHNICAL DEBT! improve user selection of watering days and times.
    if soil_type == 'sandy':
        print("Sandy soil doesn't hold water well; more frequent waterings are best to keep your plants healthy.")
        print("Three days a week should do nicely. Lets say Mon-Weds-Fri for now.")

        zone1.waterSun, zone1.waterMon, zone1.waterTue, zone1.waterWed, zone1.waterThu, zone1.waterFri, zone1.waterSat\
            = 0, 1, 0, 1, 0, 1, 0

    elif soil_type == 'loamy':
        print("Your loamy soil will hold water well. We recommend picking one watering day a week.")
        print("We'll make it easy and pick Wednesday for now.")
        zone1.waterSun, zone1.waterMon, zone1.waterTue, zone1.waterWed, zone1.waterThu, zone1.waterFri, zone1.waterSat \
            = 0, 0, 0, 1, 0, 0, 0

    # TECHNICAL DEBT! Prototype doesn't allow changing the time of day for watering.
    zone1.application_rate = 1.5
    zone1.pref_time_hrs = '09'
    zone1.pref_time_min = '00'

    print("Okay, it looks like we have everything we need to calculate your water needs. We'll do that now.")
    waterdeficit = 0
    for x in range(7):
        waterdeficit += history_items_list[x].etcalc

    print("Now to account for accumulated precipitation...")
    for x in range(7):
        waterdeficit -= history_items_list[x].precip

    zone1.water_deficit = waterdeficit
    db.add(zone1)  # add/update object


# TECHNICAL DEBT - how much did you water your lawn over the past week?

    water_algo(zone1)
    print("Beep...Bop...Boop...")
    print("Judging by the past week, you have a total water deficit of {} inches." .format(str(waterdeficit)))


    print("Creating recurring tasks...")
    task_scheduler()

    print("Setup complete. Redirecting to main menu.")
    my_sys.setup_complete = True
    db.add(my_sys)
    op_menu()


def task_scheduler():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        commentText = "SIO-LogFileReset"
        schedule.remove_all(comment=commentText)
        log_update = schedule.new(command="cd {0} ; mv {1} {1}_last ".format(clientDir, LOG_FILE_NAME) , comment=commentText)
        commentText = "SIO-Daily"
        schedule.remove_all(comment=commentText)
        daily_update = schedule.new(command="cd {0} ; ./capstoneclient/dailyactions.py dailyupdate >> {1} 2>&1".format(clientDir, LOG_FILE_NAME) , comment=commentText)
        if not DWDBG:
            #normal operation
            #every day at 3am
            daily_update.setall('0 3 * * *')
            log_update.setall('0 3 * * *')
        else:
            #every 10min
            daily_update.setall('*/10 * * * *')
            log_update.setall('*/10 * * * *')

        if on_raspi == True:
            #normal operation
            commentText = "SIO-Sensors"
            schedule.remove_all(comment=commentText)
            sensor_query = schedule.new(command="cd {0} ; ./capstoneclient/dailyactions.py readsensors >> {1} 2>&1".format(clientDir, LOG_FILE_NAME) , comment=commentText)
            sensor_query.setall('*/5 0 0 0 0')
        else:
            commentText = "SIO-DEV"
            schedule.remove_all(comment=commentText)
            dev_mode = schedule.new(command="cd {0} ; ./capstoneclient/dailyactions.py DEV >> {1} 2>&1".format(clientDir, LOG_FILE_NAME) , comment=commentText)
            # every 1 minute
            dev_mode.setall('*/1 * * * *')

        schedule.write()
        print(schedule)
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")
    return


def application_rate_cal():
    print("Lets get calibrating! We'll only do zone 1 today (since I'm only a prototype and all).")
    print("Here are the instructions for calibration.")
    print("...") # Insert instructions here
    print("...") # Insert instructions here
    print("...") # Insert instructions here
    new_application_rate = input("Now, enter your new application rate in inches per hour (as an integer or decimal value): ")

    # look to db for a zone 1 config, if none add it, if there update it
    zone_1 = db.get(SystemZoneConfig, "zone1")
    zone_1.application_rate = new_application_rate
    db.add(zone1)  # add/update object

    op_menu()


def raspi_testing():
    #TODO DW I'm not sure what Collin meant with this below comment?
    # todo figure prevent error without source
    schedule = ()  # Schedule()
    sense = ()  # Sensors()
    baro_data = sense.baro()
    soil_data = sense.soil()
    sensor_data = [datetime.datetime.now(), baro_data[1], baro_data[2], soil_data]

    print("Welcome aboard, matey.")
    print("Menu:")
    print("1: Check sensor readings.")
    print("2: Manual zone control.")
    print("3: First startup simulation")
    print("0. Exit")
    choice = input("Choose wisely. ")
    if choice == '0': 
        print("Exiting program")
        exit()
    if choice == '1':
        print("Sensor data:")
        print("Timestamp: ", sensor_data[0])
        print("Temperature: ", sensor_data[1])
        print("Barometric pressure: ", sensor_data[2])
        print("Soil moisture: ", sensor_data[3])
    elif choice == '2':
        pass  # System.Zone.manual_control()
    elif choice == '3':
        startup()
    else:
        print("You have chosen...poorly.")
        sys.exit()


##############################################
#                                            #
#                 IT BEGINS.                 #
#                 (main)                     #
#                                            #
##############################################
db = DBManager()
db.start_databases()


my_sys = db.get(SystemZoneConfig, "system")

zone1 = db.get(SystemZoneConfig, "zone1")

if on_raspi:
    raspi_testing()

if my_sys.setup_complete:
    print("---Not first startup---\n")
    op_menu()
else:
    print("First startup! Welcome.")
    startup()
