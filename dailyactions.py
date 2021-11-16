##############################################################
#  this script will be run as a crontab scheduled event,     #
#  or during startup by importing to capstoneclient.py       #
##############################################################

import sys
import time
#import requests
#import json
from datetime import date, datetime
from capstoneclient.models import SensorEntry, SystemZoneConfig, HistoryItem
from capstoneclient.db_manager import DBManager
from capstoneclient.isOnRaspi import isOnRaspi 



# Debug mode variable used to enable additional print statements 
DWDBG = False 
# DWDBG = True

on_raspi = isOnRaspi()
if on_raspi:
    # this try/except lets code function outside of raspberry pi for development.
    from capstoneclient.sensors import read_baro_sensor, read_soil_sensor, read_adc, read_adc_for
else:
    DWDBG = True
    from capstoneclient.not_raspi import read_baro_sensor, read_soil_sensor, read_adc, read_adc_for

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




# water_algo() develops the desired watering tasks and passes it to water_scheduler() to be executed with CronTab
def water_algo(zone: SystemZoneConfig) -> int:
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
    #db.start_databases()

    #DW 2021-09-18-14:49 - Collin had this set as argv[0], but that would return the script name, wouldn't it? It was not working for me. Now this is working.
    #DW the reason he had it set to 0 might be because when importing the file in capstoneclient.py it would throw and error if set to 1!
    #TODO DW 2021-09-23-13:27 need to check number of args first. Could create an error
    choice = sys.argv[1]

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

        print(f"{str(datetime.now())}---{choice}: ",end='')
        for name, val in [["temp_c", baro[0]], ["pressure", baro[2]], ["sl_moist", soil_moist], ["sl_temp", soil_temp]]:
            print(f"{name}({val}) ",end='')
        print("")
        sample = SensorEntry(datetime=datetime.now(), temp_c=baro[0], pressure_hPa=baro[2], moisture=soil_moist)
        db.add(sample)

    elif choice == "dailyupdate":
        # TODO: daily weather history updates / ET recalculations
        # TODO: rework watering tasks pursuant to ET recalculations
        #TODO make work with all zones
        my_sys = db.get(SystemZoneConfig, "system")
        zone1 = db.get(SystemZoneConfig, "zone1")

        #TODO why is my_sys.water_deficit returning None?
        waterdeficit = my_sys.water_deficit or 0.1

        #today_history_item = gethistoricaldata(latitude=my_sys.lat, longitude=my_sys.long)[0]

        probe('waterdeficit')
        probe('today_history_item.etcalc')
        #DW 2021-11-08-16:11 Commenting this stuff out for now while we just prep for demo day
#
#        waterdeficit += today_history_item.etcalc
#
#        precip = today_history_item.precip
#        waterdeficit -= precip
#        my_sys.water_deficit = waterdeficit
#        db.add(my_sys)
#
#        #TODO really should make this loop through all available zones, and for prototype it'll only be 1 
#        water_algo(zone1)

    elif choice == "STARTUP":
        import capstoneclient.cronjobs as cj # for CronTab scheduler functions
        cj.create_startup_cron()
        cj.create_static_system_crons()
        if on_raspi:
            from capstoneclient.gpio_control import *
            raspi_startup()
        else:
            print("DBG: Ran raspi_startup()")

    elif choice == "SET_STARTUP_CRON":
        import capstoneclient.cronjobs as cj # for CronTab scheduler functions
        #TODO add web gui to the @reboot crontab
        #print("DW - need to add webgui boot up to the cron job when possible")
        cj.create_startup_cron()

    elif choice == "DEV":
        print("{}---DEV: test ".format(str(datetime.now())))
    elif choice == "DEV_SOIL":
        print("{}---DEV: SOIL ".format(str(datetime.now())))
        soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]
        print(f"Soil Moisture: {soilmoisture}, Soil Temp: {soiltemp}")
    elif choice == "DEV_BARO":
        print("{}---DEV: BARO ".format(str(datetime.now())))
        baro = read_baro_sensor()   # [cTemp, fTemp, pressure, humidity] but humidity is erroneous
        print(f"Baro Sensor: {baro}")
    elif choice == "DEV_ADC":
        print("{}---DEV: ADC ".format(str(datetime.now())))
        read_adc_for("valve1_current")
        read_adc_for("5v_sense")
        read_adc_for("temp_sense")
        read_adc_for("this_should_fail")
        read_adc_for("all")
#        adc_addresses = [0x48, 0x49, 0x4a, 0x4b]
#        adc_pins = list(range(0,4))
#        for addr in adc_addresses:
#            for pin in adc_pins:
#                timenow = str(datetime.now())
#                print(f"{timenow}---READING: ADC(0x{addr:02x})-PIN({pin})")
#                val, volt = read_adc(addr, pin)
#                timenow = str(datetime.now())
#                print(f"{timenow}---ADC(0x{addr:02x})-PIN({pin}):: value: {val}, voltage: {volt}")
    elif choice == "DEV_CLEAR_ZC":
        clear_zone_control()
    elif choice == "DEV_VO":
        import zone_control 
        zone_control.open_valve(1)
    elif choice == "DEV_VC":
        import zone_control 
        zone_control.close_valve(1)
    elif choice == "DEV_RDGPIO": #Test if zone1 can be read like any other BCM pin - result: Yes
        import capstoneclient.gpio_control as gc
        import zone_control 
        import RPi.GPIO as GPIO
        gc.setup_gpio()
        zone1Val = GPIO.input(7)
        print(f"{datetime.now()}---{choice}: zone1 value = {repr(zone1Val)}")
    else:
        print(f"{datetime.now()}---INPUT PARAM CHOICE NOT RECOGNIZED: '{choice}'")
