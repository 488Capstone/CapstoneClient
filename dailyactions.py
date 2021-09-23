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
from capstoneclient.models import SensorEntry, SystemZoneConfig, HistoryItem
from capstoneclient.db_manager import DBManager

ZONE_CONTROL_COMMENT_NAME = 'SIO-ZoneControl'
LOG_FILE_NAME = './client_dev.log'

on_raspi = True
# this try/except lets code function outside of raspberry pi for development.
try:
    import smbus
    import busio
    import board 
    from board import SCL, SDA
    from adafruit_seesaw.seesaw import Seesaw
    print("Appears to be running on Raspi")
except:
    print("Importing raspi Python libs failed")
    on_raspi = False
    DWDBG = True
 

# Debug mode variable used to enable additional print statements 
DWDBG = False 
DWDBG = True
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

#####################################
#    BME280 sensor functionality    #
#####################################
def baro():
    # TODO: remove humidity artifacts from baro method
    bus = smbus.SMBus(1)  # BME280 address, 0x76(118)
    # Read data back from 0x88(136), 24 bytes
    b1 = bus.read_i2c_block_data(0x77, 0x88, 24)  # Convert the data

    # Temp coefficients
    dig_T1 = b1[1] * 256 + b1[0]
    dig_T2 = b1[3] * 256 + b1[2]
    if dig_T2 > 32767:
        dig_T2 -= 65536
    dig_T3 = b1[5] * 256 + b1[4]
    if dig_T3 > 32767:
        dig_T3 -= 65536
    # Pressure coefficients
    dig_P1 = b1[7] * 256 + b1[6]
    dig_P2 = b1[9] * 256 + b1[8]
    if dig_P2 > 32767:
        dig_P2 -= 65536
    dig_P3 = b1[11] * 256 + b1[10]
    if dig_P3 > 32767:
        dig_P3 -= 65536
    dig_P4 = b1[13] * 256 + b1[12]
    if dig_P4 > 32767:
        dig_P4 -= 65536
    dig_P5 = b1[15] * 256 + b1[14]
    if dig_P5 > 32767:
        dig_P5 -= 65536
    dig_P6 = b1[17] * 256 + b1[16]
    if dig_P6 > 32767:
        dig_P6 -= 65536
    dig_P7 = b1[19] * 256 + b1[18]
    if dig_P7 > 32767:
        dig_P7 -= 65536
    dig_P8 = b1[21] * 256 + b1[20]
    if dig_P8 > 32767:
        dig_P8 -= 65536
    dig_P9 = b1[23] * 256 + b1[22]
    if dig_P9 > 32767:
        dig_P9 -= 65536  # BME280 address, 0x77
    # Read data back from 0xA1(161), 1 byte
    dig_H1 = bus.read_byte_data(0x77, 0xA1)  # BME280 address, 0x76
    # Read data back from 0xE1(225), 7 bytes
    b1 = bus.read_i2c_block_data(0x77, 0xE1, 7)  # Convert the data

    # Humidity coefficients
    dig_H2 = b1[1] * 256 + b1[0]
    if dig_H2 > 32767:
        dig_H2 -= 65536
    dig_H3 = (b1[2] & 0xFF)
    dig_H4 = (b1[3] * 16) + (b1[4] & 0xF)
    if dig_H4 > 32767:
        dig_H4 -= 65536
    dig_H5 = (b1[4] / 16) + (b1[5] * 16)
    if dig_H5 > 32767:
        dig_H5 -= 65536
    dig_H6 = b1[6]
    if dig_H6 > 127:
        dig_H6 -= 256  # BME280 address, 0x76(118)

    # Select control humidity register, 0xF2(242)
    #		0x01(01)	Humidity Oversampling = 1
    bus.write_byte_data(0x77, 0xF2, 0x01)

    # Select Control measurement register, 0xF4(244)
    #		0x27(39)	Pressure and Temperature Oversampling rate = 1
    #					Normal mode
    bus.write_byte_data(0x77, 0xF4, 0x27)
    # BME280 address, 0x76(118)
    # Select Configuration register, 0xF5(245)
    #		0xA0(00)	Stand_by time = 1000 ms
    bus.write_byte_data(0x77, 0xF5, 0xA0)
    time.sleep(0.5)  # BME280 address, 0x76(118)
    # Read data back from 0xF7(247), 8 bytes
    # Pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB
    # Temperature xLSB, Humidity MSB, Humidity LSB
    data = bus.read_i2c_block_data(0x77, 0xF7, 8)

    # Convert pressure and temperature data to 19-bits
    adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
    adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16  # Convert the humidity data
    adc_h = data[6] * 256 + data[7]

    # Temperature offset calculations
    var1 = (adc_t / 16384.0 - dig_T1 / 1024.0) * dig_T2
    var2 = ((adc_t / 131072.0 - dig_T1 / 8192.0) * (adc_t / 131072.0 - dig_T1 / 8192.0)) * dig_T3
    t_fine = (var1 + var2)
    cTemp = (var1 + var2) / 5120.0
    fTemp = cTemp * 1.8 + 32

    # Pressure offset calculations
    var1 = (t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * dig_P6 / 32768.0
    var2 = var2 + var1 * dig_P5 * 2.0
    var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
    var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * dig_P1
    p = 1048576.0 - adc_p
    p = (p - (var2 / 4096.0)) * 6250.0 / var1
    var1 = dig_P9 * p * p / 2147483648.0
    var2 = p * dig_P8 / 32768.0
    pressure = (p + (var1 + var2 + dig_P7) / 16.0) / 100

    # Humidity offset calculations
    var_H = (t_fine - 76800.0)
    var_H = (adc_h - (dig_H4 * 64.0 + dig_H5 / 16384.0 * var_H)) * (
                dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * var_H * (1.0 + dig_H3 / 67108864.0 * var_H)))
    humidity = var_H * (1.0 - dig_H1 * var_H / 524288.0)
    if humidity > 100.0:
        humidity = 100.0
    elif humidity < 0.0:
        humidity = 0.0

    # packages everything up all nice and neat, returns as an array.
    data = [cTemp, fTemp, pressure, humidity]
    return data

#########################################
#   soil moisture sensor functionality  #
#########################################
def read_soil_sensor():
    i2c_bus = board.I2C()
    #i2c_bus = busio.I2C(SCL, SDA)
    i2c_soil = Seesaw(i2c_bus, addr=0x36)
    soilmoisture = i2c_soil.moisture_read()
    soiltemp = i2c_soil.get_temp()

    print("Soil Moisture: {0}\tSoil Temp: {1}".format(soilmoisture, soiltemp))
    return soilmoisture, soiltemp


# TODO: Read ADC.
################################
#   ADC module functionality   #
################################
def adc(): # currently working in adcsource.py
    pass


#############################################################################
#    Queries APIs weather/solar data and dumps it into db table "HISTORY"   #
#############################################################################
def gethistoricaldata(days: int = 1, latitude: float = 0., longitude=0.): #-> list[HistoryItem]:
    """Returns list of HistoryItems, one for each of preceding given days [Int] at given lat [Float], long [Float]."""

    print(f"gethistoricaldata({days}) has begun")

    def getsolar(lat_s, long_s):  # pulls solar data
        apikey, payload, headers = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ", {}, {}
        hours = 168
        url = "https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={}&latitude={}&longitude={}&hours={}&format=json".format(apikey, lat_s, long_s, hours)
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)  # pulls solar data

    def getweather(lat_w, long_w):
        window = days * 24 * 60 * 60  # seconds in a day, api max 7 days - most recent 7 to match solar data
        appid = "ae7cc145d2fea84bea47dbe1764f64c0"
        start = round(time.time()-window)
        end = round(time.time())
        # print(f'lat: {lat_w}, long: {long_w}, start: {start}, stop: {end}')
        # url = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat_w}&lon={long_w}&start={start}&end={end}&appid={appid}"
        url = "http://history.openweathermap.org/data/2.5/history/city?lat={}&lon={}&start={}&end={}&appid={}" \
            .format(lat_w, long_w, start, end, appid)
        payload, headers = {}, {}
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)  # pulls weather data

    def parseweather(lat_pw, long_pw): # -> list[HistoryItem]:  # parses weather data pulled from getweather()
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
def water_algo(zone: SystemZoneConfig) -> float:
    """Calls water_scheduler with attributes from given zone [SystemZoneConfig]. Then outputs session time [float]."""
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
    session_time = req_watering_time / len(watering_days)  # number of minutes per watering session

    water_scheduler( zoneid="zone1", days=watering_days, duration=session_time, pref_time_hrs=waterdata.pref_time_hrs, pref_time_min=waterdata.pref_time_min)
    return session_time


#################################################
#    schedules watering events using crontab    #
#################################################
def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):
    #currentDir = os.getcwd()
    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
        commentText = ZONE_CONTROL_COMMENT_NAME  
        schedule.remove_all(comment=commentText)
        #DW this var allows us to test the real schedule setting if we're in dev mode, if it remains 0 then we're in an accerated developer test mode
        #DW while we're still developing I guess it'll be nice to have the valve opening and closing at a faster rate
        setRealSched = 0
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd $SIOclientDir; ./runPy.sh ".format(clientDir)
        if on_raspi:
            command_string = "{} ./zone_control.py {} {} " .format(prescriptCmd, str(zoneid), str(duration), LOG_FILE_NAME)  # adds args to zone_control.py
        else:
            command_string = "{} ./zone_control_devmode.py {} {} " .format(prescriptCmd, str(zoneid), str(duration), LOG_FILE_NAME)  # adds args to zone_control.py
        
        if setRealSched:
            for x in range(len(days)):
                task = schedule.new(command=command_string, comment=commentText)  # creates a new entry in the crontab
                task.dow.on(days[x])  # day of week as per object passed to the method
                task.minute.on(int(pref_time_min))  # minute-hand as per object passed to the method
                task.hour.on(int(pref_time_hrs))  # hour-hand as per object passed to the method
                schedule.write()  # finalizes the task in the crontab
                print("task {} created" .format(x))
        else:
            task = schedule.new(command=command_string, comment=commentText)  # creates a new entry in the crontab
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

    #probe('choice')
    #probe('logFile')

    print("{}---dailyactions.py::{}".format(str(datetime.now()), choice))

    if choice == "readsensors":
        soil_moist, soil_temp = soil()   # value between [200, 2000]
        baro = baro()   # [cTemp, fTemp, pressure, humidity] but humidity is erroneous
        sample = SensorEntry(datetime=datetime.now, temp_c=baro[0], pressure_hPa=baro[2], moisture=soil_moist)
        db.add(sample)

    elif choice == "dailyupdate":
        # TODO: daily weather history updates / ET recalculations
        # TODO: rework watering tasks pursuant to ET recalculations
        #TODO make work with all zones
        my_sys = db.get(SystemZoneConfig, "system")
        zone1 = db.get(SystemZoneConfig, "zone1")

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
        soil = read_soil_sensor()   # value between [200, 2000]
        soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]

