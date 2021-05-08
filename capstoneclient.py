# Top level
# This is the primary python script which will incorporate all functionality.
on_raspi = True

import datetime
import json
import sqlite3 as sl

import requests
from crontab import CronTab

from etcalc import *

# from publish import *

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


# Queries APIs for last 7 days weather/solar data and dumps it into my-data.db "HISTORY" table
def gethistoricaldata():
    # initializes database & creates table for weather history
    def startdb():
        # Initializes database
        db = sl.connect('my-data.db')
        db.execute("""
            CREATE TABLE IF NOT EXISTS HISTORY (
            date TEXT UNIQUE NOT NULL PRIMARY KEY,
            windspeed REAL,
            solar REAL,
            tmax REAL,
            tmin REAL,
            rh REAL,
            pressure REAL
            );
        """)
        db.commit()
        return db

    # pulls the past week of solar data
    def getsolar():
        # gets solar data
        # TODO: only works for Collin's house. Gotta dig through the API data to fix this.
        url = "https://api.solcast.com.au/weather_sites/72dd-d2ae-0565-ae79/estimated_actuals?format=json&api_key=N5x3La865UcWH67BIq3QczgKVSu8jNEJ"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        print("response type: ",type(response))
        print("Response data: ", response)
        data = response.text
        print("response.text type:",type(data))
        return json.loads(data)

    def getweather():
        # gets weather data from the past week.
        # TODO: currently pulls weather data from static dates and Collin's location. Needs to be based on the current time/date.
        url = "http://history.openweathermap.org/data/2.5/history/city?id=4157634&type=hour&start=1619758800&end=1620277200&appid=ae7cc145d2fea84bea47dbe1764f64c0"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        # opens weather history file
        #   with open('data/weatherhistory.json') as f:
        #       data = json.load(f)
        return json.loads(response.text)

    # parses weather data pulled from getweather()
    def parseweather():
        db = sl.connect('my-data.db')
        data = getweather()
        temp = []
        dailydata = []  # this will hold the week's worth of valid data at the end.

        for x in data['list']:
            timestamp = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d%H')
            date = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d')
            windspeed = x['wind']['speed']
            pressure = x['main']['pressure']
            humidity = x['main']['humidity']
            temp_min = x['main']['temp_min']
            temp_max = x['main']['temp_max']
            entry = [[timestamp], [date], [windspeed], [pressure], [humidity], [temp_min], [temp_max]]
            temp.append(entry)

        # combines hourly data into min/max or avg daily values
        avgwind = float(temp[0][2][0])
        avgpres = float(temp[0][3][0])
        avghum = float(temp[0][4][0])
        temp_min = float(temp[0][5][0])
        temp_max = float(temp[0][6][0])
        entrycounter = 1

        for x in range(len(temp)):
            try:
                if x == (len(temp)-1):
                    entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter, (temp_min-273.15)*1.8+32, (temp_max-273.15)*1.8+32]
                    dailydata.append(entry)
                    # TODO: make sure getweather() is pulling the entire last day of weather so there isn't just one data point.
                elif temp[x][1] == temp[x+1][1]:
                    entrycounter += 1
                    avgwind += float(temp[x+1][2][0])
                    avgpres += float(temp[x+1][3][0])
                    avghum += float(temp[x+1][4][0])
                    temp_min = min(temp_min, float(temp[x][5][0]), float(temp[x+1][5][0]))
                    temp_max = max(temp_max, float(temp[x][6][0]), float(temp[x+1][6][0]))
                else:
                    entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                             (temp_min - 273.15) * 1.8 + 32, (temp_max - 273.15) * 1.8 + 32]
                    dailydata.append(entry)
                    avgwind = float(temp[x+1][2][0])
                    avgpres = float(temp[x+1][3][0])
                    avghum = float(temp[x+1][4][0])
                    temp_min = float(temp[x+1][5][0])
                    temp_max = float(temp[x+1][6][0])
                    entrycounter = 1

            except:
                print("Exception occurred while parsing historical weather data.")
                pass


        # makes entries into HISTORY table of database
        for x in range(len(dailydata)):
            cursor = db.cursor()
            cursor.execute('''INSERT OR IGNORE INTO HISTORY(date, windspeed, pressure, rh, tmin, tmax) VALUES(?,?,?,?,?,?)''', (dailydata[x][0], dailydata[x][1], dailydata[x][2], dailydata[x][3], dailydata[x][4], dailydata[x][5]))
            db.commit()

    def parsesolar():
        db = sl.connect('my-data.db') # connection to DB
        # opens solar data file
        with open('data/solardata.json') as f:
            data = json.load(f)

        # limit use of getsolar() - we only get 10 API calls per day.
        # data = getsolar()
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
                    entry = [temp[x][0], (ghi / entrycounter)*86.4e-3] # converts ghi into MJ / (day * m^2) for ET calcs
                    dailydata.append(entry)
                elif temp[x][0] == temp[x+1][0]:
                    ghi += temp[x+1][1]
                    entrycounter += 1
                else:
                    entry = [temp[x][0], (ghi / entrycounter)*86.4e-3] # converts ghi into MJ / (day * m^2) for ET calcs
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

    db = startdb()
    parseweather()
    parsesolar()


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
    gethistoricaldata()
    print("Database of historical environmental data built.")
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
    print("3: gethistoricaldata()")
    choice = input("Choose wisely. ")
    if choice == '1':
        startup()
    elif choice == '3':
        gethistoricaldata()
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