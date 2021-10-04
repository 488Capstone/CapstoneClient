import requests
import json
# import time
from datetime import date, datetime, time, timezone

class WeatherDayItem:
    
    def __init__(self, date):
        self.date = date
        #print(f"---- new weather item created with date {self.date}")
    date: date
    windspeed: float
    pressure: float
    humidity: float 
    temp_min: float 
    temp_max: float 
    precip: float

def get_weather_for_days(days: list, lat: float, long: float, offset) -> list:
    weather_list = []
    for day in days:
        #item = WeatherDayItem()
        data = fetch_weather_data(day, lat, long, offset)
        
        item = parseweather(day, data)
        #print(f"THIS ITEM CAME BACK FROM PARSEWEATHER, has date: {item.date}") # GOOD
        x = weather_list.append(item)
        #weather_tup_list.append(weather_tup)
        #print(x)
        #print(f"weather_tup_list from weather: appending weather tup with item with date = {item.date}") # GOOD
        #for x in weather_list:
            #print(f"all weather list items: {x} with date {x.date}")
    #print(f"LAST TIME leaving WEATHER: weather tup list length = {len(weather_list)}")
    #print(f"LAST TIME leaving WEATHER: weather tup list first item date = {weather_list[0].date}")
    #print(f"LAST TIME leaving WEATHER: weather tup list 2nd item date = {weather_list[1].date}") # BAD
    return weather_list




def fetch_weather_data(date, lat, long, offset) -> json:
    
    start = datetime.combine(date, time.min) + offset
    start = int(start.timestamp())
    end = datetime.combine(date, time.max) + offset
    end = int(end.timestamp())

    #print(f"start time = {start}, end time = {end}. offset = {offset}")

    appid = "ae7cc145d2fea84bea47dbe1764f64c0"

    url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
        .format(lat, long, start, end, appid)
    payload, headers = {}, {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)  # pulls weather data

def parseweather(day, data: json): # -> list[HistoryItem]:
    """Returns WeatherDayItem populated with weather data"""
    # weather_history_list = []

    tot_wind, tot_press, tot_hum, tot_precip = 0, 0, 0, 0
    temp_min = data['list'][0]['main']['temp_min']
    temp_max = data['list'][0]['main']['temp_max']
    
    for x in data['list']:
        
        tot_wind += x['wind']['speed']
        tot_press += x['main']['pressure']
        tot_hum += x['main']['humidity']
        temp_min = min(temp_min, x['main']['temp_min']) 
        temp_max = max(temp_max, x['main']['temp_max'])
        try:
            tot_precip += float(x['rain']['1h'])
        except:
            pass

    ave_wind = float(tot_wind) / len(data['list'])
    ave_press = float(tot_wind) / len(data['list']) 
    ave_hum = float(tot_wind) / len(data['list']) 
    temp_min = temp_min - 273.15
    temp_max = temp_max - 273.15
    tot_precip = tot_precip / 25.4

    new_day = WeatherDayItem(day)
    #new_day.date = day
    new_day.windspeed = ave_wind
    new_day.pressure = ave_press
    new_day.humidity = ave_hum
    new_day.temp_min = temp_min
    new_day.temp_max = temp_max
    new_day.precip = tot_precip
    
    #print(f"new day date is {new_day.date}")

    return new_day


# weather_data = json.dumps(fetch_weather_data(datetime.today().date(),-33.856784, 151.215297))
# with open("data/weather_data.json", 'w') as f:
#     f.write(weather_data)
