
import sys
import time
import requests
import json
from datetime import date, datetime
import datetime as dt
from capstoneclient.models import SensorEntry, SystemZoneConfig, HistoryItem
#from capstoneclient.isOnRaspi import * # for isOnRaspi()
#from capstoneclient.cronjobs import * # for CronTab scheduler functions
import capstoneclient.db_manager as dm

DWDBG = False
#DWDBG = True

KEY_LAST_WEATHERPULL = "last_weather_request"
KEY_RAW_WEATHER = "raw_weather_response"
KEY_WEATHER_DATA = "weather_response_data"

if __name__ == "__main__":
    DB = dm.DBManager()
    my_sys = DB.get(SystemZoneConfig, "system")

    #DB.jsonSet(DEMO_KEY_NAME, True)

def getsolar(lat_s, long_s):  # pulls solar data
    apikey, payload, headers = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ", {}, {}
    hours = 168
    url = "https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={}&latitude={}&longitude={}&hours={}&format=json".format(apikey, lat_s, long_s, hours)
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)  # pulls solar data

def DWgetweather():
    return getweather(5, my_sys.lat, my_sys.long)

def DWset_last_pull(daysago):
    daydelta_threshold = dt.timedelta(days=1)
    todaydate = dt.date.today()
    newdate = todaydate - daysago*daydelta_threshold
    settimestamp_field(KEY_LAST_WEATHERPULL, newdate)

def settimestamp_field(name, value):
    formatStr = "%Y/%m/%d"
    DB.jsonSet(name, value.strftime(formatStr))

def gettimestamp_field(name, defval=dt.date.today()):
    formatStr = "%Y/%m/%d"
    tsval = DB.jsonGet(name)
    if tsval is not None:
        tsval = dt.datetime.strptime(tsval,formatStr).date()
    else:
        tsval = defval # some big number that should make our functions execute
    return tsval


#DW Added in conditions so that we only request the weather API 1 time per a given day so we don't go over the API limit
# nocache means to force a web API request rather than using a cached version of the raw weather response.
def getweather(days, lat_w, long_w, nocache=False):
    daydelta_threshold = dt.timedelta(days=1)
    todaydate = dt.date.today()
    last_weatherpull = gettimestamp_field(KEY_LAST_WEATHERPULL, (todaydate-2*daydelta_threshold))
    #print(todaydate - last_weatherpull)
    if nocache or (todaydate - last_weatherpull >= daydelta_threshold):
        print("requesting Web API, last weather API request was NOT within the last day")
        #the return value is a list of the API responses. rtrnVal[0] will be the same day that the request was made (last_weatherpull)
        #   Each index after that is 'x' days away from the last_weatherpull date. so rtrnVal[2] is 2 days before last_weatherpull
        rtrnVal = {}
        appid = "f943dfa3da7d6883d17786a8295a9eba" #DW 2021-11-09-10:56 updated to new api key, old stopped working?
            #appid = "ae7cc145d2fea84bea47dbe1764f64c0" # old api, Collin's?
        exclude_current = "minutely,hourly"
        url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat_w}&lon={long_w}&exclude={exclude_current}&appid={appid}"
        payload, headers = {}, {}
        response = requests.request("GET", url, headers=headers, data=payload)
        rtrnVal["today"] = json.loads(response.text)  # pulls weather data
        rtrnVal["history"] = []
        for daysago in range(1, days+1):
            #window = days * 24 * 60 * 60  # seconds in a day, api max 7 days - most recent 7 to match solar data
            #start = round(time.time()-window)
            #end = round(time.time())
            # print(f'lat: {lat_w}, long: {long_w}, start: {start}, stop: {end}')
            # url = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat_w}&lon={long_w}&start={start}&end={end}&appid={appid}"
    #        url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
    #            .format(lat_w, long_w, start, end, appid)
 
            date_param = round((dt.datetime.now() - dt.timedelta(days=1)*daysago).timestamp())
            url = "https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={}&lon={}&dt={}&appid={}" \
                .format(lat_w, long_w, date_param, appid)

            #print(url)
            payload, headers = {}, {}
            response = requests.request("GET", url, headers=headers, data=payload)
            #rtrnVal[daysago] = json.loads(response.text)  # pulls weather data
            rtrnVal["history"].append(json.loads(response.text))  # pulls weather data

        settimestamp_field(KEY_LAST_WEATHERPULL, todaydate)
        DB.jsonSet(KEY_RAW_WEATHER, rtrnVal)
        for pastday in rtrnVal['history']:
            avg_weather = avg_hourly_dict(pastday['hourly'])
            pastday['hourly_avg'] = avg_weather
            #remove 'hourly' so it's not confusing
            pastday.pop('hourly')
        DB.jsonSet(KEY_WEATHER_DATA, rtrnVal)
    else:
        print("last weather API request was within the last day, pulling from cached results instead")
        rtrnVal = DB.jsonGet(KEY_WEATHER_DATA)
        #print_raw_weather(rtrnVal)
    return rtrnVal

def avg_hourly_dict(listofdict):
    #to my understanding, hourly list from weather response returns 24 dict's, with info about the status at that hour marker.
    # this func will take in that hourly list of dictionaries and return a dict which is the average of all numerical statuses.
    # currently, non-numeric info is ignored
    avg_dict = {}
    for hourdict in listofdict:
        for key in hourdict.keys():
            value = hourdict[key]
            if isinstance(hourdict[key], (int, float)):
                value = float(value)
                if key in avg_dict.keys():
                    avg_dict[key] = (value + avg_dict[key])/2
                else:
                    avg_dict[key] = value
    return avg_dict

def print_raw_weather(rawdata):
    todayData = rawdata['today']
    print(f"today val:")
    print(json.dumps(todayData, indent=4))
    print("\n\n")
    histData = rawdata['history']
    for daysago in range(0, len(histData)):
        print(f"day -{daysago+1} val:")
        print(json.dumps(histData[daysago], indent=4))
        print("\n\n")

def DWgethist():
    return gethistoricaldata(5, my_sys.lat, my_sys.long)

def printjson(jsondata):
    print(json.dumps(jsondata, indent=5))

#############################################################################
#    Queries APIs weather/solar data and dumps it into db table "HISTORY"   #
#############################################################################
def gethistoricaldata(days: int = 1, latitude: float = 0., longitude=0.): #-> list[HistoryItem]:
    """Returns list of HistoryItems, one for each of preceding given days [Int] at given lat [Float], long [Float]."""
    #TODO DW  2021-11-09-10:04 Just to get all this working for now, I'm hardcoding the days to 5
    days = 5
    print(f"gethistoricaldata({days}) has begun")

    # generate list of day items with weather data, apply solar data to matching days
    weather_list = getweather(days, latitude, longitude)

    #printjson(weather_list)

    #weather_solar_list = parsesolar(latitude, longitude, weather_list)   # Queries APIs weather/solar data and dumps it into db table "HISTORY"

    #DW 2021-11-08-16:16 removed solar from the scheme for now
    final_list = weather_list
    #final_list = []
    # apply et data to each daily item
    #for item in weather_solar_list:
    #    final_list.append(et_calculations(item))
    return final_list

def get_weather_data_for_webgui_formatnum(num):
    return f"{num:0.2f}"

def get_weather_data_for_webgui(dbarg=dm.DBManager()):
    global DB
    DB = dbarg
    my_sys = DB.get(SystemZoneConfig, "system")
    weather_data = getweather(5, my_sys.lat, my_sys.long)
    hist = weather_data['history']
    rtrnVal = {
                'today': weather_data['today'],
                'history': []
            }
 #   key_units = {
 #           '':
 #         "temp": 'C',
 #         "feels_like": 300.483564388752,
 #         "pressure": 1016.29199385643,
 #         "humidity": 15.25280487537384,
 #         "dew_point": 273.0873318362236,
 #         "uvi": 1.5307422065734864,
 #         "clouds": 1.37109375,
 #         "visibility": 10000.0,
 #         "wind_speed": 0.033081448078155516,
 #         "wind_deg": 13.453672647476196,
 #         "wind_gust": 1.34
 #           }
    for day in hist:
    #using insert flips the order, which is what we want for the webgui
        rtrnVal['history'].insert(0, dict())
        #print(rtrnVal['history'])
        curdict = rtrnVal['history'][0]
        day = day['hourly_avg']
        #print(day)
        date = dt.datetime.fromtimestamp(round(day['dt'])).date()
        date = date.strftime("%d-%b-%Y")
        curdict['Date'] = date
        avgkeys = list(day.keys())
        #loop over every key except the first ('dt') and format the key/value to be ready for webgui printing
        for avgkey in avgkeys[1:]:
            newkey = f"Avg. {avgkey}"
            curdict[newkey] = get_weather_data_for_webgui_formatnum(day[avgkey])
    return rtrnVal


#     "hourly_avg": {
#          "dt": 1637013600.0004292,
#          "temp": 302.15573389649387,
#          "feels_like": 300.483564388752,
#          "pressure": 1016.29199385643,
#          "humidity": 15.25280487537384,
#          "dew_point": 273.0873318362236,
#          "uvi": 1.5307422065734864,
#          "clouds": 1.37109375,
#          "visibility": 10000.0,
#          "wind_speed": 0.033081448078155516,
#          "wind_deg": 13.453672647476196,
#          "wind_gust": 1.34
#     }
    


############################################################################
#    calculates ET for a given date based on weather history data in db    #
############################################################################
def et_calculations(h_i: HistoryItem) -> HistoryItem:  # string passed determines what day ET is evaluated for
    """Takes a HistoryItem, returns HistoryItem with etcalc for given windspeed, solar, tmax, tmin, rh, and pressure."""
    # todo: check these have reasonable values
    history_item = h_i
    wind = history_item.windspeed  # wind - meters per second,
    # stretch: account for longwave solar radiation
    solar = history_item.solar  # shortwave solar radiation in  MJ / (m^2 * d)
    T_max = history_item.tmax  # daily max temp in Celsius
    T_min = history_item.tmin  # daily min temp in Celsius

    rh = history_item.rh / 100  # daily average relative humidity as a decimal
    pressure = history_item.pressure / 10  # database stores hectopascals (hPa), ET calc needs kilopascals (kPa)

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
    if solar is None:
        print("solar data was None. Setting to 1 to bypass issue")
        solar = 1
    et_num = 0.408 * delta * (solar - G) + psycho * (C_n / (T + 273)) * wind * (e_s - e_a)
    et_den = delta + psycho * (1 + C_d * wind)

    etmm = et_num / et_den  # millimeters per day
    et = etmm / 25.4  # inches per day

    history_item.etcalc = et
    return history_item

def parseweather(days, lat_pw, long_pw): # -> list[HistoryItem]:  # parses weather data pulled from getweather()
    """Returns list of HistoryItems populated with weather data (missing solar)"""
    weather_history_list = []

    data = getweather(days, lat_pw, long_pw)
    print(f'weather data: {data}')
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
        new_day = HistoryItem()
        new_day.date = dailydata[x][0]
        print(f'new_day.date: {new_day.date}')
        new_day.windspeed = dailydata[x][1]
        new_day.pressure = dailydata[x][2]
        new_day.rh = dailydata[x][3]
        new_day.tmin = dailydata[x][4]
        new_day.tmax = dailydata[x][5]
        new_day.precip = dailydata[x][6]
        #DB.add(new_day)
        weather_history_list.append(new_day)
    return weather_history_list

def parsesolar(lat_ps: float, long_ps: float, wl: list): #-> list[HistoryItem]:
    print("parsesolar() begins.")

    wl_ps = wl

    # opens solar data file
    with open('data/solar_sample_data.json') as f:
        data = json.load(f)
    print("file has been opened.")
    # limit use of getsolar() - we only get 10 API calls per day.
    # data = getsolar(lat_ps, long_ps)

    dailydata = []
    temp = []


    for x in data['estimated_actuals']:
        # date = x['period_end'][0:10].replace('-', '')
        entry_date = datetime.fromisoformat(x['period_end'][:-2]).date()
        entry = [entry_date, x['ghi']]
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

    print("solar value length: ", len(entry))
    # for each history item find entry w/ matching date in dailydata and update history item solar value
    # todo: depending on how well solar api and weather api date ranges match some days may have no solar data,
    #  possibly no solar data if using json list. maybe do solar first, use that range for weather
    for history_item in wl_ps:
        wl_date = history_item.date

        matching_list = list(filter(lambda e: e[0] == wl_date, dailydata))
        if len(matching_list) >= 1:
            history_item.solar = matching_list[0][1]

    return wl_ps

###################################################################
#   Example of historical weather data
###################################################################
#info can also be found on site:
#   https://openweathermap.org/api/one-call-api#current
# DW IMPORTANT! it turns out the current weather request will return a 'daily' field that has the forecast for future days!
#
#>>> import capstoneclient.weatherdata as wd
#>>> hist = wd.DWgethist()
#gethistoricaldata(5) has begun
#requesting Web API, last weather API request was NOT within the last day
#
# each entry in history is index+1 days from TODAY. so hist['history'][0] is yesterday, [1] is the day before that, etc
#>>> wd.printjson(hist['history'][0])
#{
#     "lat": 33.3121,
#     "lon": -111.8213,
#     "timezone": "America/Phoenix",
#     "timezone_offset": -25200,
#     "current": {
#          "dt": 1636994477,
#          "sunrise": 1636984735,
#          "sunset": 1637022313,
#          "temp": 293.39,
#          "feels_like": 292.1,
#          "pressure": 1022,
#          "humidity": 24,
#          "dew_point": 272.3,
#          "uvi": 1.8,
#          "clouds": 1,
#          "visibility": 10000,
#          "wind_speed": 0,
#          "wind_deg": 0,
#          "weather": [
#               {
#                    "id": 800,
#                    "main": "Clear",
#                    "description": "clear sky",
#                    "icon": "01d"
#               }
#          ]
#     },
#     "hourly_avg": {
#          "dt": 1637013600.0004292,
#          "temp": 302.15573389649387,
#          "feels_like": 300.483564388752,
#          "pressure": 1016.29199385643,
#          "humidity": 15.25280487537384,
#          "dew_point": 273.0873318362236,
#          "uvi": 1.5307422065734864,
#          "clouds": 1.37109375,
#          "visibility": 10000.0,
#          "wind_speed": 0.033081448078155516,
#          "wind_deg": 13.453672647476196,
#          "wind_gust": 1.34
#     }
#}
#>>> 
#
#
#>>> wd.printjson(hist['today'])
#{
#     "lat": 33.3121,
#     "lon": -111.8213,
#     "timezone": "America/Phoenix",
#     "timezone_offset": -25200,
#     "current": {
#          "dt": 1637080877,
#          "sunrise": 1637071191,
#          "sunset": 1637108680,
#          "temp": 293.04,
#          "feels_like": 291.79,
#          "pressure": 1017,
#          "humidity": 27,
#          "dew_point": 273.51,
#          "uvi": 1.76,
#          "clouds": 40,
#          "visibility": 10000,
#          "wind_speed": 0,
#          "wind_deg": 0,
#          "weather": [
#               {
#                    "id": 802,
#                    "main": "Clouds",
#                    "description": "scattered clouds",
#                    "icon": "03d"
#               }
#          ]
#     },
#     "daily": [
#          {
#               "dt": 1637089200,
#               "sunrise": 1637071191,
#               "sunset": 1637108680,
#               "moonrise": 1637104260,
#               "moonset": 1637061960,
#               "moon_phase": 0.42,
#               "temp": {
#                    "day": 295.58,
#                    "min": 290.89,
#                    "max": 300.73,
#                    "night": 292.76,
#                    "eve": 296.45,
#                    "morn": 291
#               },
#               "feels_like": {
#                    "day": 294.43,
#                    "night": 291.27,
#                    "eve": 295.23,
#                    "morn": 289.44
#               },
#               "pressure": 1015,
#               "humidity": 21,
#               "dew_point": 272.31,
#               "wind_speed": 2.61,
#               "wind_deg": 341,
#               "wind_gust": 3.26,
#               "weather": [
#                    {
#                         "id": 803,
#                         "main": "Clouds",
#                         "description": "broken clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 64,
#               "pop": 0,
#               "uvi": 3.2
#          },
#          {
#               "dt": 1637175600,
#               "sunrise": 1637157648,
#               "sunset": 1637195049,
#               "moonrise": 1637192340,
#               "moonset": 1637151780,
#               "moon_phase": 0.45,
#               "temp": {
#                    "day": 297.34,
#                    "min": 289.79,
#                    "max": 298.33,
#                    "night": 291.95,
#                    "eve": 294.54,
#                    "morn": 289.79
#               },
#               "feels_like": {
#                    "day": 296.21,
#                    "night": 290.43,
#                    "eve": 293.2,
#                    "morn": 288.11
#               },
#               "pressure": 1015,
#               "humidity": 15,
#               "dew_point": 268.95,
#               "wind_speed": 1.78,
#               "wind_deg": 77,
#               "wind_gust": 2.34,
#               "weather": [
#                    {
#                         "id": 804,
#                         "main": "Clouds",
#                         "description": "overcast clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 100,
#               "pop": 0,
#               "uvi": 3.05
#          },
#          {
#               "dt": 1637262000,
#               "sunrise": 1637244104,
#               "sunset": 1637281420,
#               "moonrise": 1637280540,
#               "moonset": 1637241600,
#               "moon_phase": 0.48,
#               "temp": {
#                    "day": 298.38,
#                    "min": 289.22,
#                    "max": 300.81,
#                    "night": 292.87,
#                    "eve": 295.81,
#                    "morn": 289.28
#               },
#               "feels_like": {
#                    "day": 297.32,
#                    "night": 291.47,
#                    "eve": 294.58,
#                    "morn": 287.58
#               },
#               "pressure": 1018,
#               "humidity": 14,
#               "dew_point": 268.82,
#               "wind_speed": 2.35,
#               "wind_deg": 98,
#               "wind_gust": 3.27,
#               "weather": [
#                    {
#                         "id": 800,
#                         "main": "Clear",
#                         "description": "clear sky",
#                         "icon": "01d"
#                    }
#               ],
#               "clouds": 0,
#               "pop": 0,
#               "uvi": 3.53
#          },
#          {
#               "dt": 1637348400,
#               "sunrise": 1637330560,
#               "sunset": 1637367792,
#               "moonrise": 1637368980,
#               "moonset": 1637331420,
#               "moon_phase": 0.5,
#               "temp": {
#                    "day": 295.35,
#                    "min": 289.25,
#                    "max": 298.69,
#                    "night": 293.51,
#                    "eve": 296.69,
#                    "morn": 289.25
#               },
#               "feels_like": {
#                    "day": 294.07,
#                    "night": 292.15,
#                    "eve": 295.57,
#                    "morn": 287.54
#               },
#               "pressure": 1018,
#               "humidity": 17,
#               "dew_point": 268.99,
#               "wind_speed": 2.77,
#               "wind_deg": 95,
#               "wind_gust": 3.27,
#               "weather": [
#                    {
#                         "id": 803,
#                         "main": "Clouds",
#                         "description": "broken clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 59,
#               "pop": 0,
#               "uvi": 3.65
#          },
#          {
#               "dt": 1637434800,
#               "sunrise": 1637417015,
#               "sunset": 1637454166,
#               "moonrise": 1637457660,
#               "moonset": 1637421240,
#               "moon_phase": 0.54,
#               "temp": {
#                    "day": 296.57,
#                    "min": 291,
#                    "max": 298.6,
#                    "night": 293.81,
#                    "eve": 296.39,
#                    "morn": 291
#               },
#               "feels_like": {
#                    "day": 295.44,
#                    "night": 292.48,
#                    "eve": 295.27,
#                    "morn": 289.49
#               },
#               "pressure": 1016,
#               "humidity": 18,
#               "dew_point": 271.24,
#               "wind_speed": 2.13,
#               "wind_deg": 124,
#               "wind_gust": 3.07,
#               "weather": [
#                    {
#                         "id": 804,
#                         "main": "Clouds",
#                         "description": "overcast clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 100,
#               "pop": 0,
#               "uvi": 4
#          },
#          {
#               "dt": 1637521200,
#               "sunrise": 1637503471,
#               "sunset": 1637540541,
#               "moonrise": 1637546700,
#               "moonset": 1637511060,
#               "moon_phase": 0.57,
#               "temp": {
#                    "day": 296.54,
#                    "min": 292.25,
#                    "max": 296.86,
#                    "night": 293.48,
#                    "eve": 294.75,
#                    "morn": 292.25
#               },
#               "feels_like": {
#                    "day": 295.43,
#                    "night": 292.56,
#                    "eve": 293.85,
#                    "morn": 290.82
#               },
#               "pressure": 1016,
#               "humidity": 19,
#               "dew_point": 271.24,
#               "wind_speed": 4.53,
#               "wind_deg": 10,
#               "wind_gust": 6.25,
#               "weather": [
#                    {
#                         "id": 804,
#                         "main": "Clouds",
#                         "description": "overcast clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 100,
#               "pop": 0,
#               "uvi": 4
#          },
#          {
#               "dt": 1637607600,
#               "sunrise": 1637589926,
#               "sunset": 1637626919,
#               "moonrise": 1637636040,
#               "moonset": 1637600640,
#               "moon_phase": 0.6,
#               "temp": {
#                    "day": 296.59,
#                    "min": 292.39,
#                    "max": 298.97,
#                    "night": 294.21,
#                    "eve": 297.19,
#                    "morn": 292.39
#               },
#               "feels_like": {
#                    "day": 295.64,
#                    "night": 293.29,
#                    "eve": 296.28,
#                    "morn": 291.28
#               },
#               "pressure": 1018,
#               "humidity": 25,
#               "dew_point": 275.53,
#               "wind_speed": 3.85,
#               "wind_deg": 218,
#               "wind_gust": 6.08,
#               "weather": [
#                    {
#                         "id": 804,
#                         "main": "Clouds",
#                         "description": "overcast clouds",
#                         "icon": "04d"
#                    }
#               ],
#               "clouds": 100,
#               "pop": 0.01,
#               "uvi": 4
#          },
#          {
#               "dt": 1637694000,
#               "sunrise": 1637676381,
#               "sunset": 1637713298,
#               "moonrise": 1637725680,
#               "moonset": 1637690040,
#               "moon_phase": 0.63,
#               "temp": {
#                    "day": 291.36,
#                    "min": 287.98,
#                    "max": 292.08,
#                    "night": 287.98,
#                    "eve": 290.41,
#                    "morn": 288.83
#               },
#               "feels_like": {
#                    "day": 290.96,
#                    "night": 287.37,
#                    "eve": 289.78,
#                    "morn": 288.49
#               },
#               "pressure": 1014,
#               "humidity": 66,
#               "dew_point": 284.71,
#               "wind_speed": 2.89,
#               "wind_deg": 120,
#               "wind_gust": 4.74,
#               "weather": [
#                    {
#                         "id": 500,
#                         "main": "Rain",
#                         "description": "light rain",
#                         "icon": "10d"
#                    }
#               ],
#               "clouds": 82,
#               "pop": 1,
#               "rain": 7.59,
#               "uvi": 4
#          }
#     ]
#}
#>>> 
#
###################################################################
