##############################################################
#  this script will be run as a crontab scheduled event,     #
#  or during startup by importing to capstoneclient.py       #
##############################################################

import os
import sys
from datetime import datetime, timedelta, date

from crontab import CronTab

from capstoneclient.models import SensorEntry, SystemConfig, ZoneConfig, HistoryItem
from capstoneclient.db_manager import DBManager
from capstoneclient.sensors import read_baro_sensor, read_soil_sensor
from capstoneclient.solar import solar_radiation_for_dates
from capstoneclient.weather import get_weather_for_days

ZONE_CONTROL_COMMENT_NAME = 'SIO-ZoneControl'
LOG_FILE_NAME = './client_dev.log'

def isOnRaspi ():
    return os.path.exists("/sys/firmware/devicetree/base/model")

def correct_missing_history_items():
    # check db for missing history data: up to 7 days
    missing_history_dates_list = []
    day_delta = timedelta(days = 1)
    today = datetime.today()
    for i in range(7):
        date = (today - (i * day_delta)).date()
        # check there's a history item for date
        item = db.get(HistoryItem, date)
        if not item:
            missing_history_dates_list.append(date)
    history_items_list = gethistoricaldata(missing_history_dates_list, lat=my_sys.lat, long=my_sys.long)
    for item in history_items_list:
        try:
            db.add(item)
        except Exception as e:
            print("capstoneclient startup(): cant add history item to db (probably already there)")
            db.my_session.rollback()

    # check db for missing solar data: up to 7 days
    missing_solar_dates_list = []
    for i in range(7):
        date = today - (i * day_delta)
        # check there's a history item for date
        solar = db.get_solar_for_date(date)
        if not solar > 0:
            missing_solar_dates_list.append(date)
    complete_tup_list = solar_radiation_for_dates(missing_solar_dates_list)
    for tup in complete_tup_list:
        result = db.get(HistoryItem, tup[0])
        result.solar = tup[1]
    db.commit()
    num_corrections = len(missing_history_dates_list)+len(missing_solar_dates_list)
    return num_corrections

def gethistoricaldata(day_list: list, lat: float, long: float) -> list[HistoryItem]:
    """Returns list of HistoryItems, one for each of days in list at given lat [Float], long [Float]."""

    weather_tup_list = get_weather_for_days(day_list, lat, long)
    solar_tup_list = solar_radiation_for_dates(day_list, lat, long)
    
    history_item_list = []
    for day in day_list:
        weather_tup = [tup for tup in weather_tup_list if day in tup]
        solar_tup = [tup for tup in solar_tup_list if day in tup]
        item = HistoryItem()
        item.populate_from_weather_item(weather_tup[1])
        item.solar = solar_tup[1]
        item.calculate_et_and_water_deficit()
        history_item_list.append(item)
    return history_item_list

def read_sensors():
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

def daily_update():
    # my_sys = db.get(SystemConfig, "system")
    # zone1 = db.get(ZoneConfig, "zone1")
    # zone2 = db.get(ZoneConfig, "zone2")
    # zone3 = db.get(ZoneConfig, "zone3")
    # zone4 = db.get(ZoneConfig, "zone4")
    # zone5 = db.get(ZoneConfig, "zone5")
    # zone6 = db.get(ZoneConfig, "zone6")
    # zone_list = [zone1, zone2, zone3, zone4, zone5, zone6]

    num_corrections = correct_missing_history_items()
    if num_corrections > 0:
        # recalc total deficit for past week
        rolling_water_deficit = db.get_previous_week_water_deficit
        # update auto schedule for each zone based on new daily data
        for zone_num in my_sys.zones_enabled:
            current_zone = zone_list[zone_num - 1]
            current_zone.water_algo(rolling_water_deficit)
    db.my_session.commit()

    # probe('waterdeficit')
    # probe('today_history_item.etcalc')

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

##############################################
#                                            #
#                 IT BEGINS.                 #
#                 (main)                     #
#                                            #
##############################################
#DW 2021-09-18-16:28 need to add this in so 'import' doesnt run this code
#   We only want this code running when the script is called standalone.
db = DBManager()
zone_list = db.zone_list
my_sys = db.my_sys

if __name__ == "__main__":

    
    # db.start_databases()

    #DW 2021-09-18-14:49 - Collin had this set as argv[0], but that would return the script name, wouldn't it? It was not working for me. Now this is working.
    #DW the reason he had it set to 0 might be because when importing the file in capstoneclient.py it would throw and error if set to 1!
    
    choice = None
    if sys.argv[1]:
        choice = sys.argv[1]
    else:
        print("dailyactions.py: called with no sys.arg")

    #probe('choice')
    #probe('logFile')
    print("{}---dailyactions.py::{}".format(str(datetime.now()), choice))

    if choice == "readsensors":
        read_sensors()
    if choice == "dailyupdate":
        daily_update()
    if choice == "DEV":
        print("{}---DEV: test ".format(str(datetime.now())))
    if choice == "DEV_SOIL":
        print("{}---DEV: SOIL ".format(str(datetime.now())))
        soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]
