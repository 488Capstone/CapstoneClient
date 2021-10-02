#####################################################################
# Title: capstoneclient.py                                          #
# Authors: Collin T, Doug W, Nolan B, Xavier R, Jeff M              #
# this script contains setup and operation of the device.           #
#####################################################################

import os
from re import match
import sys
import requests
import re

from crontab import CronTab

# from cron_descriptor import get_description
import datetime
from dailyactions import (
    gethistoricaldata,
    water_algo,
    ZONE_CONTROL_COMMENT_NAME,
    LOG_FILE_NAME,
    isOnRaspi,
)
from capstoneclient.db_manager import DBManager
from capstoneclient.models import SystemConfig, ZoneConfig, ScheduleEntry, Schedule

from capstoneclient.sensors import read_baro_sensor, read_soil_sensor

from zone_control import open_all, close_all




DWDBG = False

# controls imports that only work on raspberry pi. This allows code to stay functional for development on other systems.

on_raspi = isOnRaspi()
if on_raspi:
    # this try/except lets code function outside of raspberry pi for development.
    try:
        # todo: import error on RPi => adding from capstoneclient to import below
        from capstoneclient.raspispecific import *
    except Exception as e:
        on_raspi = False
        DWDBG = True
        print("Importing raspi Python libs failed")
        input(
            "not on raspi; functionality will be incomplete. Press enter to acknowledge."
        )
        print(e)
        import traceback

        errMsg = traceback.format_exc()
        print(errMsg)
else:
    DWDBG = True
    input("not on raspi; functionality will be incomplete. Press enter to acknowledge.")


# op_menu() is the landing spot for operations.
def op_menu():
    # TODO: create water budget functionality
    # TODO: allow for WaterSense prescribed watering day schedules
    print("Menu:")
    print("1. My System")
    print("2. My Schedule")
    print("3. Application Rate Calibration")
    print("4. Open all valves")
    print("5. Close all valves")
    print("6. Settings [coming soon]")
    print("7. Water budgeting [coming soon]")
    print("8. Reset system cronjobs")
    print("0. Exit")
    choice = input("Choose wisely. ")
    if choice == "0":
        print("Exiting program")
        exit()
    if choice == "1":
        my_system()
    elif choice == "2":
        my_schedule()
    elif choice == "3":
        application_rate_cal()
    elif choice == "4":
        open_all()
    elif choice == "5":
        close_all()
    elif choice == "8":
        task_scheduler()
    elif choice == "6" or "7":
        print('What is exactly do you think, "coming soon" means...?')
    else:
        print("Try again, turd")
    op_menu()


# my_system() displays basic system/zone data when requested from op_menu()
# todo: these not returning config just set up
def my_system():

    print("System Data:")
    print(f"Location: {my_sys.city}, {my_sys.state}, {my_sys.zipcode}")
    print(f"Enabled zones: {my_sys.zones_enabled}.")
    # todo sensors shown here
    print(
        f"Zone 1 soil is primarily {zone1.soil_type}. "
        f"Application rate is {zone1.application_rate} inches per hour."
    )
    
    input("Press any key to continue.")


def my_schedule():
    # schedule is zone specific, saved in zone config
    # schedule can be auto-set or manual - manual ignores all inputs, schedule is auto adjusted
    
    # auto schedule adjusts with forecast

    day_dict = {"Mon":0, "Tue":1, "Wed":2, "Thur":3, "Fri":4, "Sat":5, "Sun":6}

    def manual_zone_setup(zone_num: int):
        schedule = Schedule()
        
        i = input("Enter any desired watering days and times in this format: \n Mon 7-7:15, Mon 13-15, Tue 6-7, Wed 14:30-14:45, Thur, Fri, Sat, Sun \n ")
        
        mylist = i.split(', ')
        try:
            for item in mylist:

                item_split = item.split(' ')  # split day from times
                day_num = day_dict.get(item_split[0])  

                start_time = 0

                time_list = item_split[1].split('-')  # split to and from times
                if ':' not in time_list[0]:  # no minutes
                    start_datetime = datetime.datetime.strptime(time_list[0]+':00', '%H:%M')  # add minutes and make datetime
                    start_time = datetime.time(start_datetime)
                else:
                    start_datetime = datetime.datetime.strptime(time_list[0], '%H:%M')  # make datetime
                    start_time = datetime.time(start_datetime.hour, start_datetime.minute)
                if ':' not in time_list[1]:  # no minutes
                    finish_datetime = datetime.datetime.strptime(time_list[1]+':00', '%H:%M')  # add minutes and make datetime
                else:
                    finish_datetime = datetime.datetime.strptime(time_list[1], '%H:%M')  # make datetime

                duration_delta = (finish_datetime - start_datetime)
                duration = int(duration_delta.total_seconds() // 60)
                
                schedule_item = ScheduleEntry(day_num, start_time, duration)
                schedule.append(schedule_item)

        except Exception as e:
            print("Cannot parse: {e}")
        
        if schedule:
            zone1.schedule = schedule
            zone1.is_manual_mode = True
            db.add(zone1)
     
    print("Schedule Setup:")
    print(f"Enabled zones: {my_sys.zones_enabled}")

    for zone_num in my_sys.zones_enabled:
        if zone1.is_manual_mode:
            print(f"Zone #{zone_num}: MANUAL at these times:")
        else:
            print(f"Zone #{zone_num}: AUTO, at these times:")

        for item in zone1.schedule:
            print(item)

        
    i = input("Press 0 to edit settings for all zones, 1-6 for a specific zone, or any other key to continue.")

    if int(i) not in range(7):
        return
    auto_man = input("(A)uto or (M)anual watering control?")

    if auto_man not in ["A", "a", "M", "m"]:
        return
    if auto_man in ["A", "a"]:
        input("Automatic watering control selected. Limited to M-F, 6-10AM and 2-6PM.")
        return
    if auto_man in ["M", "m"]:
        print("Manual watering control selected.")
        manual_zone_setup(int(i))


def startup():

    my_sys.zones_enabled = [1]

    print("Excellent choice, sir. Startup protocol initiated.")

    i = input("Enabled Zones: Zone1 is enabled by default. Change? [Y]es, or any other key to continue")
    matches = False
    if i in ['Y', 'y']:
        while not matches:
            i = input("Enter a string of six numbers (0's or 1's) for new configuration. Enabled=1, Disabled=0")
            if not re.fullmatch(r"[01]{6}", i):
                print("Like this: 101001")
            else:
                print("Enabled Zones saved")
                matches = True
                new_enabled_zones = []
                for x in range(len(i)):
                    if int(i[x]) == 1:
                        new_enabled_zones.append(x+1)
                my_sys.zones_enabled = new_enabled_zones
                    


    # Get location data from IP address:
    loc = requests.get(
        "http://ipapi.co/json/?key=H02y7T8oxOo7CwMHhxvGDOP7JJqXArMPjdvMQ6XhA6X4aR4Tub"
    ).json()

    # enter location into system database:
    my_sys.city, my_sys.state, my_sys.zipcode, my_sys.lat, my_sys.long = (
        loc["city"],
        loc["region_code"],
        loc["postal"],
        loc["latitude"],
        loc["longitude"],
    )

    db.add(my_sys)  # add/update object

    print(f"We think you're in {my_sys.city}, {my_sys.state} {my_sys.zipcode}")
    print(f"Lat/long: {my_sys.lat}, {my_sys.long}")
    print("For now, we'll assume that's all true.")

    # get historical weather / solar data, build database.
    # This does the past week as a starting point for a water deficit.
    history_items_list = gethistoricaldata(
        days=7, latitude=my_sys.lat, longitude=my_sys.long
    )
    print("Database of historical environmental data built.")

    # build system info:
    print("Set up each of the enabled zones")

    for i in range(len(my_sys.zones_enabled)):
        current_zone = zone_list[my_sys.zones_enabled[i]-1]
        print("ZONE"+" "+str(i+1))
        soil_type = input(
            str()+"What is the predominant soil type in this zone? [limit answers to 'sandy' or "
            "'loamy']"
        )
        while soil_type != ("sandy" or "loamy"):
            soil_type = input(
                "Sorry, we didn't quite catch that...is the predominant soil type in this zone sandy or "
                "loamy?"
            )

        current_zone.soil_type = soil_type

        # TECHNICAL DEBT! improve user selection of watering days and times.
        if soil_type == "sandy":
            print(
                "Sandy soil doesn't hold water well; more frequent waterings are best to keep your plants healthy."
            )
            print("Three days a week should do nicely. Lets say Mon-Weds-Fri for now.")

            (
                zone1.waterSun,
                zone1.waterMon,
                zone1.waterTue,
                zone1.waterWed,
                zone1.waterThu,
                zone1.waterFri,
                zone1.waterSat,
            ) = (0, 1, 0, 1, 0, 1, 0)

        elif soil_type == "loamy":
            print(
                "Your loamy soil will hold water well. We recommend picking one watering day a week."
            )
            print("We'll make it easy and pick Wednesday for now.")
            (
                current_zone.waterSun,
                current_zone.waterMon,
                current_zone.waterTue,
                current_zone.waterWed,
                current_zone.waterThu,
                current_zone.waterFri,
                current_zone.waterSat,
            ) = (0, 0, 0, 1, 0, 0, 0)

        # TECHNICAL DEBT! Prototype doesn't allow changing the time of day for watering.
        current_zone.application_rate = 1.5
        current_zone.pref_time_hrs = "09"
        current_zone.pref_time_min = "00"
        db.add(current_zone)  # add/update object

        print(
            "Okay, it looks like we have everything we need to calculate your water needs. We'll do that now."
        )  

    # TECHNICAL DEBT - how much did you water your lawn over the past week?

    water_deficit = db.get_previous_week_water_deficit()
    print(f"Judging by the past week, you have a total water deficit of {water_deficit} inches.")
    
    water_algo(current_zone, my_sys.water_deficit)
    print("Beep...Bop...Boop...")
    

    print("Creating recurring tasks...")
    task_scheduler()

    print("Setup complete. Redirecting to main menu.")
    my_sys.setup_complete = True
    db.add(my_sys)
    op_menu()


def task_scheduler():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    clientDir = os.getenv("SIOclientDir")
    if clientDir is not None:
        # DW 2021-09-20-08:29 prescriptCmd is expected to run before the cron job executed scripts, it will set the env var that
        #   tells subsequent scripts/programs what the location of the client side code is
        prescriptCmd = "cd {}; ".format(clientDir)
        commentText = "SIO-LogFileReset"
        schedule.remove_all(comment=commentText)
        log_update = schedule.new(
            command="{0} mv -v {1} {1}_last >> {1} 2>&1".format(
                prescriptCmd, LOG_FILE_NAME
            ),
            comment=commentText,
        )
        # DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd += "./runPy.sh "
        commentText = "SIO-Daily"
        schedule.remove_all(comment=commentText)
        daily_update = schedule.new(
            command=" {0} ./dailyactions.py dailyupdate ".format(
                prescriptCmd, LOG_FILE_NAME
            ),
            comment=commentText,
        )
        if not DWDBG:
            # normal operation
            # every day at 3am
            daily_update.setall("0 3 * * *")
            # every 14 days at 3am?
            log_update.setall("0 3 */14 * *")
        else:
            # every 10min
            daily_update.setall("*/10 * * * *")
            log_update.setall("*/50 * * * *")

        if on_raspi:
            # normal operation
            commentText = "SIO-Sensors"
            schedule.remove_all(comment=commentText)
            sensor_query = schedule.new(
                command="{0} ./dailyactions.py readsensors".format(
                    prescriptCmd, LOG_FILE_NAME
                ),
                comment=commentText,
            )
            sensor_query.setall("*/5 * * * *")
        else:
            commentText = "SIO-DEV"
            schedule.remove_all(comment=commentText)
            dev_mode = schedule.new(
                command="{0} ./dailyactions.py DEV".format(prescriptCmd, LOG_FILE_NAME),
                comment=commentText,
            )
            # every 1 minute
            dev_mode.setall("*/1 * * * *")

        schedule.write()
        print(schedule)
    else:
        print(
            "env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient"
        )
    return


def application_rate_cal():
    print(
        "Lets get calibrating! We'll only do zone 1 today (since I'm only a prototype and all)."
    )
    print("Here are the instructions for calibration.")
    print("...")  # Insert instructions here
    print("...")  # Insert instructions here
    print("...")  # Insert instructions here
    new_application_rate = input(
        "Now, enter your new application rate in inches per hour (as an integer or decimal value): "
    )

    # look to db for a zone 1 config, if none add it, if there update it
    zone_1 = db.get(ZoneConfig, "zone1")
    zone_1.application_rate = new_application_rate
    db.add(zone1)  # add/update object


def raspi_testing():
    # TODO DW I'm not sure what Collin meant with this below comment?
    # todo figure prevent error without source
    # schedule = Schedule()
    # sense = Sensors()
    baro_data = [0, 0, 0]
    soil_data = [0, 0]
    try:
        soil_data = read_soil_sensor()
    except Exception as e:
        print(f" Read Failed, {repr(e)}")
    try:
        baro_data = read_baro_sensor()

    except Exception as e:
        print(f" Read Failed, {repr(e)}")
    sensor_data = [datetime.datetime.now(), baro_data[1], baro_data[2], soil_data]

    print("Welcome aboard, matey.")
    print("Menu:")
    print("1: Check sensor readings.")
    print("2: Manual zone control.")
    print("3: First startup simulation")
    print("0. Exit")
    choice = input("Choose wisely. ")
    if choice == "0":
        print("Exiting program")
        exit()
    if choice == "1":
        print("Sensor data:")
        print("Timestamp: ", sensor_data[0])
        print("Temperature: ", sensor_data[1])
        print("Barometric pressure: ", sensor_data[2])
        print("Soil moisture, temperature: ", sensor_data[3])
    elif choice == "2":
        pass 
    elif choice == "3":
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


my_sys = db.get(SystemConfig, "system")
zone1 = db.get(ZoneConfig, "zone1")
zone2 = db.get(ZoneConfig, "zone2")
zone3 = db.get(ZoneConfig, "zone3")
zone4 = db.get(ZoneConfig, "zone4")
zone5 = db.get(ZoneConfig, "zone5")
zone6 = db.get(ZoneConfig, "zone6")

zone_list = [zone1, zone2, zone3, zone4, zone5, zone6]

if on_raspi:
    raspi_testing()

if my_sys.setup_complete:
    print("---Not first startup---\n")
    op_menu()
else:
    print("First startup! Welcome.")
    startup()
