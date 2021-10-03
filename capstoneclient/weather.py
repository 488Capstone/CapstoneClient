import requests
import json
# import time
from datetime import date, datetime, time

class WeatherDayItem:
    date: date
    windspeed: float
    pressure: float
    humidity: float 
    temp_min: float 
    temp_max: float 
    precip: float

def get_weather_for_days(days: list, lat: float, long: float) -> list:
    weather_tup_list = []
    for day in days:
        data = fetch_weather_data(day, lat, long)
        item = parseweather(data)
        weather_tup = (day, item)
        weather_tup_list.append(weather_tup)
    return weather_tup_list




def fetch_weather_data(date, lat, long) -> json:

    start = int(datetime.combine(date, time.min).timestamp())
    end = int(datetime.combine(date, time.max).timestamp())

    # days = 1
    # window = days * 24 * 60 * 60  # seconds in a day, api max 7 days - most recent 7 to match solar data
    appid = "ae7cc145d2fea84bea47dbe1764f64c0"
    # start = round(time.time()-window)
    # end = round(time.time())

    url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
        .format(lat, long, start, end, appid)
    payload, headers = {}, {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)  # pulls weather data


def parseweather(data: json): # -> list[HistoryItem]:
    """Returns WeatherDayItem populated with weather data"""
    # weather_history_list = []

    temp, dailydata = [], []
    for x in data['list']:
        timestamp = datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d%H')
        date_pw = date.fromtimestamp(int(x['dt']))
        windspeed = x['wind']['speed']
        pressure = x['main']['pressure']
        humidity = x['main']['humidity']
        temp_min = x['main']['temp_min']
        temp_max = x['main']['temp_max']
        try:
            precip = x['rain']['1h']
        except:
            precip = 0
        entry = [timestamp, date_pw, windspeed, pressure, humidity, temp_min, temp_max, precip]
        temp.append(entry)

    # combines hourly data into min/max or avg daily values
    avgwind, avgpres, avghum = float(temp[0][2]), float(temp[0][3]), float(temp[0][4])
    temp_min, temp_max = float(temp[0][5]), float(temp[0][6])
    try:
        precip = float(temp[0][7])
    except:
        precip = 0
    entrycounter = 1

    for x in range(len(temp)):
        try:
            if x == (len(temp)-1):
                entry = [temp[x][1], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                            temp_min-273.15, temp_max-273.15, precip / 25.4]
                dailydata.append(entry)
            elif temp[x][1] == temp[x+1][1]:
                entrycounter += 1
                avgwind += float(temp[x+1][2])
                avgpres += float(temp[x+1][3])
                avghum += float(temp[x+1][4])
                temp_min = min(temp_min, float(temp[x][5]), float(temp[x+1][5]))
                temp_max = max(temp_max, float(temp[x][6]), float(temp[x+1][6]))
                try:
                    precip += float(temp[x+1][7])
                except:
                    precip = 0
            else:
                entry = [temp[x][1], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                            temp_min - 273.15, temp_max - 273.15, precip / 25.4]
                dailydata.append(entry)
                avgwind, avgpres, avghum = float(temp[x+1][2]), float(temp[x+1][3]), float(temp[x+1][4])
                temp_min, temp_max = float(temp[x+1][5]), float(temp[x+1][6])
                try:
                    precip = float(temp[x+1][7])
                except:
                    precip = 0
                entrycounter = 1
        except:
            print("Exception occurred while parsing historical weather data.")
            pass

    for x in range(len(dailydata)):
        new_day = WeatherDayItem
        new_day.date = dailydata[x][0]
        new_day.windspeed = dailydata[x][1]
        new_day.pressure = dailydata[x][2]
        new_day.humidity = dailydata[x][3]
        new_day.temp_min = dailydata[x][4]
        new_day.temp_max = dailydata[x][5]
        new_day.precip = dailydata[x][6]
        # weather_history_list.append(new_day)

    return new_day


# weather_data = json.dumps(fetch_weather_data(datetime.today().date(),-33.856784, 151.215297))
# with open("data/weather_data.json", 'w') as f:
#     f.write(weather_data)
