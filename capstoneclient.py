#####################################################################
# Title: capstoneclient.py                                          #
# Authors: Collin T, Doug W, Nolan B, Xavier R, Jeff M              #
# this script contains setup and operation of the device.           #
#####################################################################

import json
import sqlite3 as sl
import sys
import requests
from crontab import CronTab
import datetime
import time
import publish
from dailyactions import *


# controls imports that only work on raspberry pi. This allows code to stay functional for development on other systems.
on_raspi = True
try:
    from raspispecific import *
except:
    input("not on raspi; functionality will be incomplete. Press enter to acknowledge.")
    on_raspi = False


# startdatabases() initializes necessary sqlite databases and is used in the startup functionality.
def start_databases():
    db = sl.connect('my-data.db')
    # SENSORS table holds readings from device sensors.
    db.execute("""
        CREATE TABLE IF NOT EXISTS SENSORS (
        timestamp INT UNIQUE NOT NULL PRIMARY KEY,
        cTemp REAL, pressurehPa REAL, soilmoisture REAL
        );
    """)
    db.commit()
    # HISTORY table holds weather/solar history data from API used to estimate ET and water deficit.
    db.execute("""
        CREATE TABLE IF NOT EXISTS HISTORY (
        date TEXT UNIQUE NOT NULL PRIMARY KEY,
        windspeed REAL, solar REAL, tmax REAL, tmin REAL, rh REAL, pressure REAL, precip REAL, etcalc REAL             
        );
    """)
    db.commit()
    # SYSTEM table holds data on both zones and the system as a whole. Some columns are only for zone/system data.
    db.execute("""
        CREATE TABLE IF NOT EXISTS SYSTEM (
        id TEXT UNIQUE NOT NULL PRIMARY KEY,
        zipcode INT, city TEXT, state TEXT, lat REAL, long REAL,
        soiltype TEXT, planttype TEXT, microclimate TEXT, slope REAL,
        waterSun INT, waterMon INT, waterTue INT, waterWed INT, waterThu INT, waterFri INT, waterSat INT,
        pref_time_hrs TEXT, pref_time_min TEXT,
        applicationrate REAL, waterdeficit REAL,
        setup_complete INT
        );
    """)
    db.commit()





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
    choice = input("Choose wisely. ")
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
def my_system():
    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("select city, state, zipcode from system where  id = 'system'")
    systemdata = cursor.fetchone()
    cursor.execute("select soiltype, applicationrate from system where  id = 'zone1'")
    zonedata = cursor.fetchone()

    print("System Data:")
    print("Location: {}, {}, {}" .format(systemdata[0], systemdata[1], systemdata[2]))
    print("Zone 1 soil is primarily {}. Application rate is {} inches per hour." .format(zonedata[0], zonedata[1]))
    input("Press any key to continue.")
    op_menu()


# my_schedule() displays basic scheduling data when requested from op_menu()
def my_schedule():
    # TECHNICAL DEBT! This code is not hardened against all possible inputs.
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    days = [] # init empty array

    # dump every ZoneControl task into days array:
    for tasks in schedule:
        if tasks.comment == "ZoneControl":                                                                             #
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
    city, state, zipcode, lat, long = loc['city'], loc['region_code'], loc['postal'], loc['latitude'], loc['longitude']
    print("We think you're in {}, {} {}" .format(city, state, zipcode))
    print("Lat/long: {}, {}" .format(lat, long))
    print("For now, we'll assume that's all true.")

    # enter location into system database:
    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO SYSTEM(id, city, state, zipcode, lat, long) VALUES('system', ?,?,?,?,?)", (city, state, zipcode, lat, long))
    db.commit()

    # get historical weather / solar data, build database. This does the past week as a starting point for a water deficit.
    gethistoricaldata(days = 7)
    print("Database of historical environmental data built.")

    # build system info:
    print("Lets talk about Zone 1, since this is a limited prototype and all.")
    soiltype = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or ""'loamy']")
    while soiltype != ("sandy" or "loamy"):
        soiltype = input("Sorry, we didn't quite catch that...is the predominant soil type in this zone sandy or loamy?")
    cursor.execute("INSERT OR IGNORE INTO SYSTEM(id, soiltype) VALUES('zone1', ?)", (soiltype,))
    db.commit()

    # TECHNICAL DEBT! improve user selection of watering days and times.
    if soiltype == 'sandy':
        print("Sandy soil doesn't hold water well; more frequent waterings are best to keep your plants healthy.")
        print("Three days a week should do nicely. Lets say Mon-Weds-Fri for now.")
        cursor.execute("UPDATE SYSTEM SET waterSun = ?, waterMon = ?, waterTue = ?, waterWed = ?, waterThu = ?, waterFri = ?, waterSat = ? WHERE id = ?", (0,1,0,1,0,1,0, 'zone1'))
        db.commit()
    elif soiltype == 'loamy':
        print("Your loamy soil will hold water well. We recommend picking one watering day a week.")
        print("We'll make it easy and pick Wednesday for now.")
        cursor.execute("UPDATE SYSTEM SET waterSun = ?, waterMon = ?, waterTue = ?, waterWed = ?, waterThu = ?, waterFri = ?, waterSat = ? WHERE id = ?", (0,0,0,1,0,0,0, 'zone1'))
        db.commit()

    # TECHNICAL DEBT! Prototype doesn't allow changing the time of day for watering.
    cursor.execute("UPDATE SYSTEM SET applicationrate = 1.5, pref_time_hrs = '09', pref_time_min = '00' WHERE id = 'zone1'")
    db.commit()

    print("Okay, it looks like we have everything we need to calculate your water needs. We'll do that now.")
    waterdeficit = 0
    for x in range(7):
        date = (datetime.date.today() - datetime.timedelta(days=x+1)).strftime("%Y%m%d")
        waterdeficit += et_calculations(date)
    cursor.execute("UPDATE SYSTEM SET waterdeficit = ? WHERE id = ?", (waterdeficit, 'zone1'))
    db.commit()

    print("Now to account for accumulated precipitation...")
    for x in range(7):
        date = (datetime.date.today() - datetime.timedelta(days=x + 1)).strftime("%Y%m%d")
        db = sl.connect('my-data.db')  # connect to database for historical data
        cursor = db.cursor()
        cursor.execute("select precip from history where date = ?", (date,))
        precip = cursor.fetchone()
        waterdeficit -= precip[0]
        cursor.execute(
            "UPDATE SYSTEM SET waterdeficit = ? WHERE id = ?", (waterdeficit, 'zone1'))
        db.commit()

# TECHNICAL DEBT - how much did you water your lawn over the past week?

    water_algo()
    print("Beep...Bop...Boop...")
    print("Judging by the past week, you have a total water deficit of {} inches." .format(str(waterdeficit)))

    cursor.execute(
        "UPDATE SYSTEM SET setup_complete = 1 WHERE id = 'system'")
    db.commit()

    print("Creating recurring tasks...")
    task_scheduler()

    print("Setup complete. Redirecting to main menu.")
    op_menu()


def task_scheduler():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)

    daily_update = schedule.new(command="./dailyactions.py dailyupdate", comment="Recurring")
    daily_update.setall('0 3 * * *')

    if on_raspi == True:
        sensor_query = schedule.new(command="./dailyactions.py readsensors", comment="Recurring")
        sensor_query.setall('*/5 0 0 0 0')

    schedule.write()
    print(schedule)
    return

def application_rate_cal():
    print("Lets get calibrating! We'll only do zone 1 today (since I'm only a prototype and all).")
    print("Here are the instructions for calibration.")
    print("...") # Insert instructions here
    print("...") # Insert instructions here
    print("...") # Insert instructions here
    new_application_rate = input("Now, enter your new application rate in inches per hour (as an integer or decimal value): ")
    db = sl.connect('my-data.db')  # connect to database for historical data
    cursor = db.cursor()
    cursor.execute(
        "UPDATE SYSTEM SET applicationrate = ? WHERE id = 'zone1'", (new_application_rate,))
    db.commit()
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

    if choice == '1':
        print("Sensor data:")
        print("Timestamp: ", sensor_data[0])
        print("Temperature: ", sensor_data[1])
        print("Barometric pressure: ", sensor_data[2])
        print("Soil moisture: ", sensor_data[3])
    elif choice == '2':
        System.Zone.manual_control()
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

start_databases()

db = sl.connect('my-data.db')  # connect to database for historical data
cursor = db.cursor()
cursor.execute("select setup_complete from system where id = 'system'")
startup_complete = cursor.fetchone()
try:
    if startup_complete[0] != True:
        print("---Not first startup---\n")
        if on_raspi:
            raspi_testing()
    else:
        op_menu()
except:
    print("First startup! Welcome.")
    startup()