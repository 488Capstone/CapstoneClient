# Top level
# This is the primary python script which will incorporate all functionality.

import json
import sqlite3 as sl
import sys
import requests
from crontab import CronTab
import datetime
import time
# from publish import *
#from dailyactions import gethistoricaldata, et_calculations, water_scheduler
from dailyactions import *

on_raspi = True
try:
    from raspispecific import *
except:
    print('code not executing from raspi, functionality may be incomplete (capstoneclient.py)')
    on_raspi = False


def startdatabases():
    db = sl.connect('my-data.db')
    # initialize "SENSORS" table:
    db.execute("""
        CREATE TABLE IF NOT EXISTS SENSORS (
        timestamp INT UNIQUE NOT NULL PRIMARY KEY,
        cTemp REAL,
        pressurehPa REAL,
        soilmoisture REAL
        );
    """)
    db.commit()
    # initialize "HISTORY" table:
    db.execute("""
        CREATE TABLE IF NOT EXISTS HISTORY (
        date TEXT UNIQUE NOT NULL PRIMARY KEY,
        windspeed REAL,
        solar REAL,
        tmax REAL,
        tmin REAL,
        rh REAL,
        pressure REAL,
        precip REAL,
        etcalc REAL
        );
    """)
    db.commit()
    # initialize "SYSTEM" table:
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

def water_algo():
    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("select applicationrate, waterdeficit, waterSun, waterMon, waterTue, waterWed, waterThu, waterFri, waterSat, pref_time_hrs, pref_time_min from system where id = 'zone1'")
    waterdata = cursor.fetchone()
    watering_days = []
    if waterdata[2]==1: watering_days.append("SUN")
    if waterdata[3]==1: watering_days.append("MON")
    if waterdata[4]==1: watering_days.append("TUE")
    if waterdata[5]==1: watering_days.append("WED")
    if waterdata[6]==1: watering_days.append("THU")
    if waterdata[7]==1: watering_days.append("FRI")
    if waterdata[8]==1: watering_days.append("SAT")
    emitterefficiency = {"rotary": 0.7}
    effectiveapplicationrate = waterdata[0] * emitterefficiency["rotary"]
    req_watering_time = (waterdata[1] / effectiveapplicationrate) * 60  # total number of minutes needed
    session_time = req_watering_time / len(watering_days)  # number of minutes per session
    water_scheduler(zoneid = "zone1", days = watering_days, duration = session_time, pref_time_hrs = waterdata[9], pref_time_min = waterdata[10])
    return session_time
# TODO: update op_menu() to use database
# TODO: allow for water budget feature
# TODO: allow for WaterSense prescribed watering day schedules
def op_menu():
    print("Menu:")
    print("1. My System [coming soon]")
    print("2. My Schedule [in progress]")
    print("3. Application Rate Calibration")
    choice = input("Choose wisely. ")
    if choice == '1':
        my_system()
    elif choice == '2':
        print("Watering days: ", system.zone1.watering_days)
        print("Session length: ", system.zone1.session_time, "minutes per watering session")
        print("Watering time: ", system.zone1.pref_time_hrs, system.zone1.pref_time_min)
        input("Press any key to continue.")
        op_menu()
    elif choice == '3':
        application_rate_cal()
    else:
        print('Try again, turd')
        op_menu()

# TODO: update my_system() to use database
def my_system():
    print("System Data:")
    print("Location: ", system.city, system.state, system.zipcode)
    print("Yard info: ", system.zone1.soiltype, "with", system.zone1.planttype)
    print("Watering days: ", system.zone1.watering_days)
    input("Press any key to continue.")
    op_menu()


def my_schedule():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    print("Schedule:\n",schedule)


    op_menu()

def startup():
    print('Excellent choice, sir. Startup protocol initiated.')
    db = sl.connect('my-data.db')

    # Get location data from IP address:
    loc = requests.get('http://ipapi.co/json/?key=H02y7T8oxOo7CwMHhxvGDOP7JJqXArMPjdvMQ6XhA6X4aR4Tub').json()
    city, state, zipcode, lat, long = loc['city'], loc['region_code'], loc['postal'], loc['latitude'], loc['longitude']

    print("We think you're in {}, {} {}" .format(city, state, zipcode))
    print("Lat/long: {}, {}" .format(lat, long))
    print("For now, we'll assume that's all true.")
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO SYSTEM(id, city, state, zipcode, lat, long) VALUES('system', ?,?,?,?,?)", (city, state, zipcode, lat, long))
    db.commit()

    # get historical weather / solar data:
    gethistoricaldata(days = 7)
    print("Database of historical environmental data built.")

    # build system info:
    print("Lets talk about Zone 1, since this is a limited prototype and all.")
    soiltype = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or "
                                  "'loamy']")
    cursor.execute("INSERT OR IGNORE INTO SYSTEM(id, soiltype) VALUES('zone1', ?)", (soiltype,))
    db.commit()

    # TODO: improve user selection of watering days
    if soiltype == 'sandy':
        print("Your sandy soil won't hold water well; more frequent applications of water are best to keep your "
              "plants healthy.")
        print("We recommend watering your lawn frequently - three days a week should do nicely.")
        print("We'll make it easy and say Mon-Weds-Fri for now.")  # placeholder for user selection
        cursor.execute("UPDATE SYSTEM SET waterSun = ?, waterMon = ?, waterTue = ?, waterWed = ?, waterThu = ?, waterFri = ?, waterSat = ? WHERE id = ?", (0,1,0,1,0,1,0, 'zone1'))
        db.commit()
    elif soiltype == 'loamy':
        print("Your loamy soil will hold water well. We recommend picking one watering day a week.")
        print("We'll make it easy and pick Wednesday for now.")  # placeholder for user selection
        cursor.execute("UPDATE SYSTEM SET waterSun = ?, waterMon = ?, waterTue = ?, waterWed = ?, waterThu = ?, waterFri = ?, waterSat = ? WHERE id = ?", (0,0,0,1,0,0,0, 'zone1'))
        db.commit()

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

    water_algo()
    print("Beep...Bop...Boop...")
    print("Judging by the past week, you have a total water deficit of {} inches." .format(str(waterdeficit)))

    cursor.execute(
        "UPDATE SYSTEM SET setup_complete = 1 WHERE id = 'system'")
    db.commit()
    print("Setup complete. Redirecting to main menu.")
    op_menu()


def application_rate_cal():
    print("Lets get calibrating! We'll only do zone 1 today (since I'm only a prototype and all).")
    print("Here are the instructions for calibration.")
    print("...")
    print("...")
    print("...")
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




##############################################################
#                                                            #
#                                                            #
#                                                            #
#                         It Begins.                         #
#                                                            #
#                                                            #
#                                                            #
##############################################################

startdatabases()

db = sl.connect('my-data.db')  # connect to database for historical data
cursor = db.cursor()
cursor.execute("select setup_complete from system where id = 'system'")
startup_complete = cursor.fetchone()
if startup_complete[0] == 1:
    print("---Not first startup---")
    if on_raspi:
        raspi_testing()
    else:
        op_menu()
else:
    print("First startup! Welcome.")
    startup()