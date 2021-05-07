import datetime
import json
import sqlite3 as sl

import requests


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
        # print(entry)

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
                print("hum on {} was {}" .format(temp[x][1], temp[x][4][0]))
                # TODO: make sure getweather() is pulling the entire last day of weather so there isn't just one data point.
            elif temp[x][1] == temp[x+1][1]:
                entrycounter += 1
                avgwind += float(temp[x+1][2][0])
                avgpres += float(temp[x+1][3][0])
                avghum += float(temp[x+1][4][0])
                temp_min = min(temp_min, float(temp[x][5][0]), float(temp[x+1][5][0]))
                temp_max = max(temp_max, float(temp[x][6][0]), float(temp[x+1][6][0]))
                print("hum on {} was {}" .format(temp[x][1], temp[x][4][0]))
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
            print("Exception occurred")
            pass


    # makes entries into HISTORY table of database
    for x in range(len(dailydata)):
        #print(dailydata[x][1][0])
        cursor = db.cursor()
        cursor.execute('''INSERT OR IGNORE INTO HISTORY(date, windspeed, pressure, rh, tmin, tmax) VALUES(?,?,?,?,?,?)''', (dailydata[x][0], dailydata[x][1], dailydata[x][2], dailydata[x][3], dailydata[x][4], dailydata[x][5]))
        print("made commit")
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
            print("Exception occurred")
            pass

    for x in range(len(dailydata)):
        cursor = db.cursor()
        cursor.execute("UPDATE HISTORY SET solar = ? WHERE date = ?", (dailydata[x][1], dailydata[x][0]))
        print(dailydata[x])
        print(type(dailydata[x][1]))
    db.commit()

db = startdb()
parseweather()
parsesolar()