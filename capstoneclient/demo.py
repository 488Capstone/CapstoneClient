
import time
from datetime import timedelta, datetime
import capstoneclient.zone_control_defs as zc
import capstoneclient.db_manager as dm
from capstoneclient.isOnRaspi import * # for isOnRaspi()

on_raspi = isOnRaspi()
if on_raspi:
    # this try/except lets code function outside of raspberry pi for development.
    from capstoneclient.sensors import read_baro_sensor, read_soil_sensor, read_adc, read_adc_for
else:
    DWDBG = True
    from capstoneclient.not_raspi import read_baro_sensor, read_soil_sensor, read_adc, read_adc_for

DEMO_KEY_NAME = 'en_demo_water_mode'

def query_demo_exit():
    db = dm.DBManager()
    return (not db.jsonGet(DEMO_KEY_NAME))

def demo_init():
    print(f"########################")
    print(f"Entering Demo Water Mode")
    print(f"########################")
    db = dm.DBManager()
    db.jsonSet(DEMO_KEY_NAME, True)

def disable_demo_water_mode():
    db = dm.DBManager()
    db.jsonSet(DEMO_KEY_NAME, False)

def demo_water_mode():
    ENABLE_TIME = 420 # seconds
    demo_init()
    timelimit = timedelta(seconds=ENABLE_TIME)
    start_time = datetime.now()
    exit_demo_mode = False
    soilmoist_threshold = 500
    soiltemp_threshold = 15
    open_time_sec = 3.5
    close_time_sec = 0.5
    skip_time_sec = 1.5
    while ((datetime.now() - start_time) < timelimit):
        #TODO read db to make sure we're not supposed to exit
        exit_demo_mode = query_demo_exit()
        if exit_demo_mode:
            break
        
        soil_moist, soil_temp = read_soil_sensor()   # value between [200, 2000]
        print(f"Soil Moisture: {soil_moist}, Soil Temp: {soil_temp}")
        #print("",flush=True,end='')
        moisture_cond = soil_moist < soilmoist_threshold
        temp_cond = soil_temp > soiltemp_threshold
        if moisture_cond and temp_cond:
            zc.open_valve(1)
            #print("",flush=True,end='')
            time.sleep(open_time_sec)
            zc.close_valve(1)
            #print("",flush=True,end='')
            time.sleep(close_time_sec)
        else:
            if not temp_cond:
                print(f"Temperature is too low, skipping this watering session")
            if not moisture_cond:
                print(f"Moisture is too high, extra water unnecessary, skipping this watering session")
            #print("",flush=True,end='')
            time.sleep(skip_time_sec)
        #DW flush output so we see in log file
        #print("",flush=True,end='')

    zc.close_valve(1)
    print(f"########################")
    print(f"Exiting Demo Water Mode")
    print(f"########################")
        #now_time = datetime.now()
        #total_on_dur_sec = (now_time - start_time).total_seconds()
        #print(f"{now_time}---zone_control.py:: solenoid pulsed ON time = {total_on_dur_sec} sec")



if __name__ == "__main__":
    demo_water_mode()
