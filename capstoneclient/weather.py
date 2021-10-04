import requests
import json
from datetime import datetime, time, date

class WeatherDayItem:
    
    def __init__(self, date):
        self.date = date
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
        data = fetch_weather_data(day, lat, long, offset)
        item = parseweather(day, data)
        weather_list.append(item)
    return weather_list

def fetch_weather_data(date, lat, long, offset) -> json:
    
    start = datetime.combine(date, time.min) + offset
    start = int(start.timestamp())
    end = datetime.combine(date, time.max) + offset
    end = int(end.timestamp())
    # TODO: not zero local time
    #print(f"start time = {start}, end time = {end}. offset = {offset}")

    appid = "ae7cc145d2fea84bea47dbe1764f64c0"

    url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
        .format(lat, long, start, end, appid)
    payload, headers = {}, {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)  # pulls weather data

def parseweather(day, data: json): # -> list[HistoryItem]:
    """Returns WeatherDayItem populated with weather data"""

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
    new_day.windspeed = ave_wind
    new_day.pressure = ave_press
    new_day.humidity = ave_hum
    new_day.temp_min = temp_min
    new_day.temp_max = temp_max
    new_day.precip = tot_precip
    
    return new_day
