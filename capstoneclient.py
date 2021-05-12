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

on_raspi = True
try:
    from raspispecific import *
except:
    print('code not executing from raspi, functionality may be incomplete')
    on_raspi = False


def et_calculations(date):  # string passed determines what day ET is evaluated for
    db = sl.connect('my-data.db')  # connect to database for historical data
    cursor = db.cursor()
    cursor.execute("select * from history where date = ?", (date,))
    dbdata = cursor.fetchone()
    wind = dbdata[1]  # wind - meters per second,
    # TODO: account for longwave solar radiation
    solar = dbdata[2]  # shortwave solar radiation in  MJ / (m^2 * d)
    T_max = dbdata[3]  # daily max temp in Celsius
    T_min = dbdata[4]  # daily min temp in Celsius
    rh = dbdata[5] / 100  # daily average relative humidity as a decimal
    pressure = dbdata[6] / 10  # database stores hectopascals (hPa), ET calc needs kilopascals (kPa)

    # daily mean air temp in Celsius:
    T = (T_max + T_min) / 2

    # from ASCE, G << R_n so G can be neglected. This can be improved later if desirable.
    G = 0

    e_omean = 0.6108 ** ((17.27 * T) / (T + 237.3))
    e_omin = 0.6108 ** ((17.27 * T_min) / (T_min + 237.3))
    e_omax = 0.6108 ** ((17.27 * T_max) / (T_max + 237.3))
    e_s = (e_omin + e_omax) / 2
    e_a = rh * e_omean

    delta = (2503 ** ((17.27 * T) / (T + 237.3))) / ((T + 237.3) ** 2)
    psycho = 0.000665 * pressure  # from ASCE standardized reference
    C_n = 900  # constant from ASCE standardized reference
    C_d = 0.34  # constant from ASCE standardized reference

    et_num = 0.408 * delta * (solar - G) + psycho * (C_n / (T + 273)) * wind * (e_s - e_a)
    et_den = delta + psycho * (1 + C_d * wind)

    etmm = et_num / et_den  # millimeters per day
    et = etmm / 25.4 # inches per day

    # enters calculated ET into HISTORY database
    cursor = db.cursor()
    cursor.execute("UPDATE HISTORY SET etcalc = ? WHERE date = ?", (et, date))
    db.commit()
    return et


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
        applicationrate REAL, waterdeficit REAL
        );
    """)
    db.commit()


def water_algo():
    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("select applicationrate, waterdeficit, waterSun, waterMon, waterTue, waterWed, waterThu, waterFri, waterSat from system where id = 'zone1'")
    waterdata = cursor.fetchone()
    print("waterdata: ",waterdata)
    emitterefficiency = {"rotary": 0.7}
    watering_days = sum(waterdata[2:8])
    effectiveapplicationrate = waterdata[0] * emitterefficiency["rotary"]
    req_watering_time = (waterdata[1] / effectiveapplicationrate) * 60  # number of min system will be on
    session_time = req_watering_time / watering_days  # number of minutes per session
    # since slope is assumed to be zero, every watering session will be continuous.
    #plan = Schedule(zone='zone1', duration=session_time, day=self.watering_days,
                    #hour=self.pref_time_hrs, minute=self.pref_time_min)
    #Schedule.water_scheduler(plan)
    return session_time


def water_scheduler(zoneid, duration):
    # TODO: water scheduler needs to query db.SYSTEM for watering days and watering time
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    command_string = "./zone_control.py {} {}" .format(str(zoneid), str(duration))  # adds args to zone_control.py
    task = schedule.new(command=command_string, comment='ZoneControl')  # creates a new entry in the crontab
    #TODO: fix scheduling for multiple days
    task.dow.on(day)  # day of week as per object passed to the method
    task.minute.on(minute)  # minute-hand as per object passed to the method
    task.hour.on(hour)  # hour-hand as per object passed to the method
    schedule.write()  # finalizes the task in the crontab
    print("all tasks created")
    input("Press any key to continue.")


def clear_tasks():
    schedule = CronTab(user=True)
    schedule.remove_all(comment='ZoneControl')


# Queries APIs weather/solar data and dumps it into db table "HISTORY"
# TODO: gethistoricaldata() should take in arg for days of data requested
def gethistoricaldata(days): # "days" arg determines number of days

    # pulls solar data
    def getsolar(lat, long):
        apikey, payload, headers = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ", {}, {}
        hours = 168
        url = "https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={}&latitude={}&longitude={}&hours={}&format=json".format(apikey, lat, long, hours)
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)

    # pulls weather data
    def getweather(lat, long):
        # TODO: Update to use lat/long.
        window = days * 24 * 60 * 60 + 86400 # seconds in a day, plus a one-day buffer.
        appid = "ae7cc145d2fea84bea47dbe1764f64c0"
        start = round(time.time()-window)
        end = round(time.time())
        url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
            .format(lat, long, start, end, appid)
        payload, headers = {}, {}
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)

    # parses weather data pulled from getweather()
    def parseweather(lat, long):
        db = sl.connect('my-data.db')
        data = getweather(lat, long)
        temp, dailydata = [], []
        for x in data['list']:
            timestamp = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d%H')
            date = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d')
            windspeed = x['wind']['speed']
            pressure = x['main']['pressure']
            humidity = x['main']['humidity']
            temp_min = x['main']['temp_min']
            temp_max = x['main']['temp_max']
            try:
                precip = x['rain']['1h']
            except:
                precip = 0
            entry = [[timestamp], [date], [windspeed], [pressure], [humidity], [temp_min], [temp_max], [precip]]
            temp.append(entry)

        # combines hourly data into min/max or avg daily values
        avgwind, avgpres, avghum = float(temp[0][2][0]), float(temp[0][3][0]), float(temp[0][4][0])
        temp_min, temp_max = float(temp[0][5][0]), float(temp[0][6][0])
        try:
            precip = float(temp[0][7][0])
        except:
            precip = 0
        entrycounter = 1

        for x in range(len(temp)):
            try:
                if x == (len(temp)-1):
                    entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                             temp_min-273.15, temp_max-273.15, precip / 25.4]
                    dailydata.append(entry)
                elif temp[x][1] == temp[x+1][1]:
                    entrycounter += 1
                    avgwind += float(temp[x+1][2][0])
                    avgpres += float(temp[x+1][3][0])
                    avghum += float(temp[x+1][4][0])
                    temp_min = min(temp_min, float(temp[x][5][0]), float(temp[x+1][5][0]))
                    temp_max = max(temp_max, float(temp[x][6][0]), float(temp[x+1][6][0]))
                    try:
                        precip += float(temp[x+1][7][0])
                    except:
                        precip = 0
                else:
                    entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                             temp_min - 273.15, temp_max - 273.15, precip / 25.4]
                    dailydata.append(entry)
                    avgwind, avgpres, avghum = float(temp[x+1][2][0]), float(temp[x+1][3][0]), float(temp[x+1][4][0])
                    temp_min, temp_max = float(temp[x+1][5][0]), float(temp[x+1][6][0])
                    try:
                        precip = float(temp[x+1][7][0])
                    except:
                        precip = 0
                    entrycounter = 1
            except:
                print("Exception occurred while parsing historical weather data.")
                pass

        # makes entries into HISTORY table of database
        for x in range(len(dailydata)):
            cursor = db.cursor()
            cursor.execute('''INSERT OR IGNORE INTO HISTORY(date, windspeed, pressure, rh, tmin, tmax, precip) VALUES(?,?,?,
            ?,?,?,?)''', (dailydata[x][0], dailydata[x][1], dailydata[x][2], dailydata[x][3], dailydata[x][4],
                        dailydata[x][5], dailydata[x][6]))
            db.commit()

    def parsesolar(lat, long):
        db = sl.connect('my-data.db')  # connection to DB
        # opens solar data file
        with open('data/solardata.json') as f:
            data = json.load(f)

        # limit use of getsolar() - we only get 10 API calls per day.
        #data = getsolar(lat, long)

        dailydata = []
        temp = []

        for x in data['estimated_actuals']:
            date = x['period_end'][0:10].replace('-', '')
            entry = [date, x['ghi']]
            temp.append(entry)

        ghi = temp[0][1]
        entrycounter = 1

        for x in range(len(temp)):
            try:
                if x == (len(temp)-1):
                    entry = [temp[x][0], (ghi / entrycounter)*0.0864]  # converts ghi into MJ / (day * m^2)
                    dailydata.append(entry)
                elif temp[x][0] == temp[x+1][0]:
                    ghi += temp[x+1][1]
                    entrycounter += 1
                else:
                    entry = [temp[x][0], (ghi / entrycounter)*0.0864]  # converts ghi into MJ / (day * m^2)
                    dailydata.append(entry)
                    ghi = temp[x][1]
                    entrycounter = 1
            except:
                print("Exception occurred while parsing historical solar data.")
                pass

        for x in range(len(dailydata)):
            cursor = db.cursor()
            cursor.execute("UPDATE HISTORY SET solar = ? WHERE date = ?", (dailydata[x][1], dailydata[x][0]))
        db.commit()

    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("select lat, long, cityid from system where id = 'system'")
    data = cursor.fetchone()
    lat, long, cityid = data[0], data[1], data[2]

    parsesolar(lat, long)
    parseweather(lat, long)


# TODO: update op_menu() to use database
# TODO: allow for water budget feature
# TODO: allow for WaterSense prescribed watering day schedules
def op_menu():
    print("Menu:")
    print("1. My System [coming soon]")
    print("2. My Schedule [coming soon]")
    print("3. Application Rate Calibration [coming soon]")
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
        pass
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

    cursor.execute("UPDATE SYSTEM SET applicationrate = 1.5 WHERE id = 'zone1'")
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


def testing():
    print("Welcome aboard, matey. What'll it be?")
    print("1: First startup simulation")
    # TODO: application rate calibrations
    print("2: Application rate calibration [coming soon]")
    print("3: gethistoricaldata()")
    print("4. ET calculation testing")
    choice = input("Choose wisely. ")
    if choice == '1':
        startup()
    elif choice == '3':
        gethistoricaldata(7)
    elif choice == '4':
        et_calculations('20210507')
    else:
        print('You have chosen...poorly.')
        sys.exit()


# It begins.
startdatabases()

if on_raspi:
    raspi_testing()
else:
    testing()
