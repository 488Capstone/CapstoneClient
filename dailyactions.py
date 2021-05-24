##############################################################
#  this script will be run as a crontab scheduled event,     #
#  or during startup by importing to capstoneclient.py       #
#                                                            #
#                                                            #
#                                                            #
#                                                            #
#                                                            #
##############################################################

import sys
import sqlite3 as sl
import time
import requests
import json
import datetime
from crontab import CronTab

# this try/except lets code function outside of raspberry pi for development.
try:
    import smbus
    import busio
    from board import SCL, SDA
    from adafruit_seesaw.seesaw import Seesaw
except:
    print('code not executing from raspi, functionality may be incomplete (dailyactions.py)')

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
def soil():
    soilmoisture = Seesaw(busio.I2C(SCL, SDA), addr=0x36).moisture_read()
    return soilmoisture

# TODO: Read ADC.
################################
#   ADC module functionality   #
################################
def adc(zone): # currently working in adcsource.py
    pass

#############################################################################
#    Queries APIs weather/solar data and dumps it into db table "HISTORY"   #
#############################################################################
def gethistoricaldata(days): # "days" arg determines number of days
    print("gethistoricaldata() has begun")
    def getsolar(lat, long):  # pulls solar data
        apikey, payload, headers = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ", {}, {}
        hours = 168
        url = "https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={}&latitude={}&longitude={}&hours={}&format=json".format(apikey, lat, long, hours)
        response = requests.request("GET", url, headers=headers, data=payload)
        return json.loads(response.text)# pulls solar data# pulls solar data  # pulls solar data  # pulls solar data  # pulls solar data

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
        return json.loads(response.text)  # pulls weather data

    def parseweather(lat, long):  # parses weather data pulled from getweather()
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
        print("parsesolar() begins.")
        db = sl.connect('my-data.db')  # connection to DB
        # opens solar data file
        with open('data/solardata.json') as f:
            data = json.load(f)
        print("file has been opened.")
        # limit use of getsolar() - we only get 10 API calls per day.
        data = getsolar(lat, long)

        dailydata = []
        temp = []
        print("length: ", len(data))

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

        print("solar value length: ",len(entry))

        for x in range(len(dailydata)):
            cursor = db.cursor()
            cursor.execute("UPDATE HISTORY SET solar = ? WHERE date = ?", (dailydata[x][1], dailydata[x][0]))
        db.commit()

    db = sl.connect('my-data.db')
    cursor = db.cursor()
    cursor.execute("select lat, long from system where id = 'system'")
    data = cursor.fetchone()
    lat, long = data[0], data[1]

    parseweather(lat, long)
    parsesolar(lat, long)   # Queries APIs weather/solar data and dumps it into db table "HISTORY"

############################################################################
#    calculates ET for a given date based on weather history data in db    #
############################################################################
def et_calculations(date):  # string passed determines what day ET is evaluated for
    db = sl.connect('my-data.db')  # connect to database for historical data
    cursor = db.cursor()
    cursor.execute("select * from history where date = ?", (date,))
    dbdata = cursor.fetchone()
    print("et_calculations - dbdata: ",dbdata)
    wind = dbdata[1]  # wind - meters per second,
    # stretch: account for longwave solar radiation
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


#################################################
#    schedules watering events using crontab    #
#################################################
def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    schedule.remove_all(comment='ZoneControl')
    command_string = "./zone_control.py {} {}" .format(str(zoneid), str(duration))  # adds args to zone_control.py
    for x in range(len(days)):
        task = schedule.new(command=command_string, comment='ZoneControl')  # creates a new entry in the crontab
        task.dow.on(days[x])  # day of week as per object passed to the method
        task.minute.on(int(pref_time_min))  # minute-hand as per object passed to the method
        task.hour.on(int(pref_time_hrs))  # hour-hand as per object passed to the method
        schedule.write()  # finalizes the task in the crontab
        print("task {} created" .format(x))
    input("All tasks created. Press enter to continue.")


choice = sys.argv[0]

db = sl.connect('my-data.db')
cursor = db.cursor()

if choice == "readsensors":
    soil = soil()   # value between [200, 2000]
    baro = baro()   # [cTemp, fTemp, pressure, humidity] but humidity is erroneous
    cursor.execute("INSERT OR IGNORE INTO HISTORY(timestamp, cTemp, pressurehPa, soilmoisture) VALUES(?,?,?,?)", (time.time(), baro[0], baro[2], soil))
    db.commit()

elif choice == "dailyupdate":
    # TODO: daily weather history updates / ET recalculations
    # TODO: rework watering tasks pursuant to ET recalculations
    gethistoricaldata(days = 1)
    et_calculations((datetime.date.today()).strftime("%Y%m%d"))

