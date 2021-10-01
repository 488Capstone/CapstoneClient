##############################################################
#  this script will be run as a crontab scheduled event,     #
#  or during startup by importing to capstoneclient.py       #
##############################################################

import os
import sys
import time
import requests
import json
from datetime import date, datetime
from crontab import CronTab
from capstoneclient.models import SensorEntry, SystemConfig, ZoneConfig, HistoryItem
from capstoneclient.db_manager import DBManager

from capstoneclient.sensors import read_baro_sensor, read_soil_sensor

ZONE_CONTROL_COMMENT_NAME = 'SIO-ZoneControl'
LOG_FILE_NAME = './client_dev.log'

def isOnRaspi ():
    return os.path.exists("/sys/firmware/devicetree/base/model")

on_raspi = isOnRaspi()
if on_raspi:
    # this try/except lets code function outside of raspberry pi for development.
    pass


else:
    DWDBG = True

# Debug mode variable used to enable additional print statements 
DWDBG = False 
# DWDBG = True
#DWDBG = 10 # set DWDBG to a number to change the amount of print statements! scale of 0-10, 10 being the most 
# 1 means print statements that print maybe 1-2 lines. If the number is higher, expect more prints 
################################################################################ 
# The below function is a convenience function used during debug to test the  
# values of expressions/variables periodically throughout the code. When DWDBG 
# is false it will do nothing. 
# DW 2021-06-26-10:17 - found a problem, eval() only works with globals. -Fixed, used stack frame info from 1 stack above current level 
################################################################################ 
if DWDBG: 
    def probe(expr): 
        frame = sys._getframe(1) 
        evalval = repr(eval(expr,frame.f_globals, frame.f_locals)) 
        print("***Probe: '{}' => '{}'".format(expr, evalval)) 
else: 
    # if we're not in a debug mode, just return safely! 
    def probe(expr): 
        return 0 


#############################################################################
#    Queries APIs weather/solar data and dumps it into db table "HISTORY"   #
#############################################################################
def gethistoricaldata(days: int = 1, latitude: float = 0., longitude=0.): #-> list[HistoryItem]:
    """Returns list of HistoryItems, one for each of preceding given days [Int] at given lat [Float], long [Float]."""

    print(f"gethistoricaldata({days}) has begun")

    def getsolar(lat_s, long_s):  # pulls solar data
        apikey, payload, headers = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ", {}, {}
        # todo: remind mysolf why i'm not using days here, gets a week of data when 1 day is default
        hours = 168
        url = "https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={}&latitude={}&longitude={}&hours={}&format=json".format(apikey, lat_s, long_s, hours)
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)  # pulls solar data

    def getweather(lat_w, long_w):
        window = days * 24 * 60 * 60  # seconds in a day, api max 7 days - most recent 7 to match solar data
        appid = "ae7cc145d2fea84bea47dbe1764f64c0"
        start = round(time.time()-window)
        end = round(time.time())

        url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
            .format(lat_w, long_w, start, end, appid)
        payload, headers = {}, {}
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)  # pulls weather data

    def parseweather(lat_pw, long_pw): # -> list[HistoryItem]:
        """Returns list of HistoryItems populated with weather data (missing solar)"""
        weather_history_list = []

        data = getweather(lat_pw, long_pw)
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

    # generate list of day items with weather data, apply solar data to matching days
    weather_list = parseweather(latitude, longitude)
    weather_solar_list = parsesolar(latitude, longitude, weather_list)   # Queries APIs weather/solar data and dumps it into db table "HISTORY"
    final_list = []
    # apply et data to each daily item
    for item in weather_solar_list:
        final_list.append(et_calculations(item))
    return final_list


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


# water_algo() develops the desired watering tasks and passes it to water_scheduler() to be executed with CronTab
def water_algo(zone: ZoneConfig) -> int:
    """Calls water_scheduler with attributes from given zone [SystemZoneConfig]. Then outputs session time [int]."""
    waterdata = zone
    watering_days = []
    if waterdata.waterSun == 1:
        watering_days.append("SUN")
    if waterdata.waterMon == 1:
        watering_days.append("MON")
    if waterdata.waterTue == 1:
        watering_days.append("TUE")
    if waterdata.waterWed == 1:
        watering_days.append("WED")
    if waterdata.waterThu == 1:
        watering_days.append("THU")
    if waterdata.waterFri == 1:
        watering_days.append("FRI")
    if waterdata.waterSat == 1:
        watering_days.append("SAT")

    # TECHNICAL DEBT! Prototype only accounts for rotary sprinklers
    emitterefficiency = {"rotary": 0.7}
    effectiveapplicationrate = waterdata.application_rate * emitterefficiency["rotary"]
    req_watering_time = (waterdata.water_deficit / effectiveapplicationrate) * 60  # total number of minutes needed
    session_time = int(req_watering_time / len(watering_days))  # number of minutes per watering session
    if session_time < 0:
        session_time = 0

    water_scheduler(zoneid="zone1", days=watering_days, duration=session_time, pref_time_hrs=waterdata.pref_time_hrs,
                    pref_time_min=waterdata.pref_time_min)
    return session_time


#################################################
#    schedules watering events using crontab    #
#################################################
def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):

    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
        commentText = ZONE_CONTROL_COMMENT_NAME  
        schedule.remove_all(comment=commentText)
        #DW this var allows us to test the real schedule setting if we're in dev mode, if it remains 0 then we're in an accerated developer test mode
        #DW while we're still developing I guess it'll be nice to have the valve opening and closing at a faster rate
        setRealSched = False
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd {}; ./runPy.sh ".format(clientDir)
        if on_raspi:
            command_string = "{} ./zone_control.py {} " .format(prescriptCmd, str(zoneid))  #, LOG_FILE_NAME)   adds args to zone_control.py
        else:
            command_string = "{} ./zone_control_devmode.py {} {} " .format(prescriptCmd, str(zoneid), str(duration)) #  , LOG_FILE_NAME)  # adds args to zone_control.py
        
        if setRealSched:
            for x in range(len(days)):
                # NB: turning on for duration doesnt work well.. keeps raspi locked up for minutes/hours in
                # zone_control.py.  best way to have cron run python every 15 min or so, python handles turning on/off
                # during those times but for now: make two chron entries, one on and one off (after duration).. third
                # value now on_off
                # todo: fix finish time on next day

                # adding three terms: second tells zone to go on or off, 1st tells zone it is a timed watering,
                # wait for off signal. Can set other than 0 for a short duration (raspi inside this script for duration)
                new_command_string = command_string+f"0 on {LOG_FILE_NAME}"
                task = schedule.new(command=new_command_string,
                                    comment=commentText)  # creates a new entry in the crontab
                task.dow.on(days[x])  # day of week as per object passed to the method
                task.minute.on(int(pref_time_min))  # minute-hand as per object passed to the method
                task.hour.on(int(pref_time_hrs))  # hour-hand as per object passed to the method

                schedule.write()  # finalizes the task in the crontab
                print("task {} created".format(x))

                new_command_string = command_string + f"0 off {LOG_FILE_NAME}"
                task = schedule.new(command=new_command_string,
                                    comment=commentText)  # creates a new entry in the crontab
                task.dow.on(days[x])  # day of week as per object passed to the method
                finish_minute = pref_time_min + duration
                finish_hour = pref_time_hrs
                if finish_minute > 59:
                    finish_hour += finish_hour // 60
                    finish_minute = finish_minute % 60

                task.minute.on(int(finish_minute))  # minute-hand as per object passed to the method
                task.hour.on(int(finish_hour))  # hour-hand as per object passed to the method

                schedule.write()  # finalizes the task in the crontab
                print("task {} created" .format(x))
        else:
            # use short duration function, 1 minute => no off chron
            new_command_string = command_string + f"1 on {LOG_FILE_NAME}"
            task = schedule.new(command=new_command_string, comment=commentText)  # creates a new entry in the crontab
            task.setall('*/5 * * * *') # run every 5min
            schedule.write()  # finalizes the task in the crontab
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")


##############################################
#                                            #
#                 IT BEGINS.                 #
#                 (main)                     #
#                                            #
##############################################
#DW 2021-09-18-16:28 need to add this in so 'import' doesnt run this code
#   We only want this code running when the script is called standalone.
if __name__ == "__main__":

    db = DBManager()
    db.start_databases()

    #DW 2021-09-18-14:49 - Collin had this set as argv[0], but that would return the script name, wouldn't it? It was not working for me. Now this is working.
    #DW the reason he had it set to 0 might be because when importing the file in capstoneclient.py it would throw and error if set to 1!
    #TODO DW 2021-09-23-13:27 need to check number of args first. Could create an error
    choice = sys.argv[1]

    if not choice:
        print("dailyactions.py: called with no sys.arg")

    #probe('choice')
    #probe('logFile')

    print("{}---dailyactions.py::{}".format(str(datetime.now()), choice))

    if choice == "readsensors":
        soil_moist = 0
        soil_temp = 0
        baro = [0, 0, 0]
        try:
            soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]
        except Exception as e:
            devName = "Soil Moist/Temp Sensor"
            print("{0} Read Failed.\t{1}".format(devName, repr(e)))
            import traceback
            errMsg = traceback.format_exc()
            print(errMsg)
        try:
            baro = read_baro_sensor()   # [cTemp, fTemp, pressure, humidity] but humidity is erroneous
        except Exception as e:
            devName = "Baro Sensor"
            print("{0} Read Failed.\t{1}".format(devName, repr(e)))
            import traceback
            errMsg = traceback.format_exc()
            print(errMsg)

        sample = SensorEntry(datetime=datetime.now(), temp_c=baro[0], pressure_hPa=baro[2], moisture=soil_moist)
        db.add(sample)

    elif choice == "dailyupdate":
        # TODO: daily weather history updates / ET recalculations
        # TODO: rework watering tasks pursuant to ET recalculations
        #TODO make work with all zones
        my_sys = db.get(SystemConfig, "system")
        zone1 = db.get(ZoneConfig, "zone1")

        #TODO why is my_sys.water_deficit returning None?
        waterdeficit = my_sys.water_deficit or 0.1

        today_history_item = gethistoricaldata(latitude=my_sys.lat, longitude=my_sys.long)[0]

        probe('waterdeficit')
        probe('today_history_item.etcalc')

        waterdeficit += today_history_item.etcalc

        precip = today_history_item.precip
        waterdeficit -= precip
        my_sys.water_deficit = waterdeficit
        db.add(my_sys)

        #TODO really should make this loop through all available zones, and for prototype it'll only be 1 
        water_algo(zone1)

    elif choice == "DEV":
        print("{}---DEV: test ".format(str(datetime.now())))
    elif choice == "DEV_SOIL":
        print("{}---DEV: SOIL ".format(str(datetime.now())))
        soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]

