
import time
from capstoneclient.sensors import read_soil_sensor, read_adc, read_adc_for
from datetime import timedelta, datetime
import capstoneclient.zone_control_defs as zc

def demo_water_mode():
    print(f"########################")
    print(f"Entering Demo Water Mode")
    print(f"########################")
    ENABLE_TIME = 40 # seconds
    timelimit = timedelta(seconds=ENABLE_TIME)
    start_time = datetime.now()
    exit_demo_mode = False
    soilmoist_threshold = 500
    soiltemp_threshold = 15
    while ((datetime.now() - start_time) < timelimit):
        #TODO read db to make sure we're not supposed to exit
        #exit_demo_mode = read db
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
            time.sleep(5)
            zc.close_valve(1)
            #print("",flush=True,end='')
        else:
            if not temp_cond:
                print(f"Temperature is too low, skipping this watering session")
            if not moisture_cond:
                print(f"Moisture is too high, extra water unnecessary, skipping this watering session")
            #print("",flush=True,end='')
            time.sleep(2)
        #DW flush output so we see in log file
        #print("",flush=True,end='')
        time.sleep(2)

    zc.close_valve(1)
    print(f"########################")
    print(f"Exiting Demo Water Mode")
    print(f"########################")
        #now_time = datetime.now()
        #total_on_dur_sec = (now_time - start_time).total_seconds()
        #print(f"{now_time}---zone_control.py:: solenoid pulsed ON time = {total_on_dur_sec} sec")



if __name__ == "__main__":
    demo_water_mode()
