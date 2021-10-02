from datetime import datetime, time, timedelta
from typing import List
from sqlalchemy import Column, Boolean, Integer, Float, String, DateTime, Date, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.sqltypes import Enum, PickleType

import calendar


Base = declarative_base()

# USERS table holds the registered users for this device. Currently should only be 1
class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)

    def __repr__(self):
        return f"<Users: id={self.id}, " \
               f"username={self.username}, " \
               f"password = {self.password}>"

# The original users table from the webgui looked lik:
#-- create table for our login uname & pw
#CREATE TABLE user (
#  id INTEGER PRIMARY KEY AUTOINCREMENT,
#  username TEXT UNIQUE NOT NULL,
#  password TEXT NOT NULL
#);

# SENSORS table holds readings from device sensors.
class SensorEntry(Base):
    __tablename__ = "sensor_entries"
    datetime = Column(DateTime, primary_key=True)
    temp_c = Column(Float)
    pressure_hPa = Column(Float)
    moisture = Column(Float)

    def __repr__(self):
        return f"<SensorEntry: datetime={self.datetime}, " \
               f"temp_c={self.temp_c}, " \
               f"pressure_hPa={self.pressure_hPa}, " \
               f"moisture = {self.moisture}>"


# HISTORY table holds weather/solar history data from API used to estimate ET and water deficit.
class HistoryItem(Base):
    __tablename__ = "weather_history_data"
    date = Column(Date, primary_key=True)
    windspeed = Column(Float)
    solar = Column(Float)
    tmax = Column(Float)
    tmin = Column(Float)
    rh = Column(Float)
    pressure = Column(Float)
    precip = Column(Float)
    etcalc = Column(Float)

    def __repr__(self):
        return f"<HistoryItem date={self.date}, " \
               f"windspeed={self.windspeed}, " \
               f"solar={self.solar}, " \
               f"tmax = {self.tmax}, " \
               f"tmin = {self.tmin}, " \
               f"rh = {self.rh}, " \
               f"pressure = {self.pressure}, " \
               f"precip = {self.precip}, " \
               f"etcalc = {self.etcalc}>"


# SYSTEM table holds data on both zones and the system as a whole. Some columns are only for zone/system data.
class SystemConfig(Base):
    __tablename__ = "system_configuration"
    id = Column(String, primary_key=True)
    zipcode = Column(Integer)
    city = Column(String)
    state = Column(String)
    lat = Column(Float)
    long = Column(Float)
    setup_complete = Column(Boolean)
    water_deficit = Column(Float)

    def __repr__(self):
        return f"<System Config: \n" \
               f"zipcode={self.zipcode}, \n" \
               f"city={self.city}, \n" \
               f"state = {self.state}, \n" \
               f"latitude = {self.lat}, \n" \
               f"longitude = {self.long}, \n" \
               f"setup complete = {self.setup_complete}, \n" \
               f"water_deficit = {self.water_deficit} >"

class ZoneConfig(Base):
    __tablename__ = "zone_configuration"
    id = Column(String, primary_key=True)
    soil_type = Column(String)
    # todo: plant_type, microclimate, slope
    # plant_type = Column(String)
    # microclimate = Column(String)
    # slope = Column(Float)
    waterSun = Column(Integer)
    waterMon = Column(Integer)
    waterTue = Column(Integer)
    waterWed = Column(Integer)
    waterThu = Column(Integer)
    waterFri = Column(Integer)
    waterSat = Column(Integer)
    pref_time_hrs = Column(String)
    pref_time_min = Column(String)
    application_rate = Column(Float)
    schedule = Column(PickleType)
    scheduleString = Column(String)
    manual_schedule = Column(Boolean)



class ScheduleEntry():
    """A water start event: day, time, duration"""
    def __init__(self, day_num: int, start_time: time, duration: timedelta) -> None:  # day_num Monday = 0
        
        self.day_num = day_num
        self.start_time = start_time
        self.duration = duration
    
    day_num = 0
    start_time = time(0,0)
    duration = timedelta(0)
    
    def __repr__(self):
        return f"{calendar.day_name[self.day_num]} at {self.start_time.strftime('%H:%M')} for {self.duration} minutes"
                       

class Schedule(List):
    """Holds ScheduleEntry events"""
    def add_entries(self, days: List, times: List, duration: int):
        for day in days:
            for t in times:
                new_entry = ScheduleEntry(day, t, duration)
                self.append(new_entry)
        
    def clear_entries(self):
        self.clear()

    def get_next_entry(self) -> str: 
        """ Returns next watering entry after now"""
        
        # filter on day = today
        match = [i for i in self if i.day_num == datetime.today().weekday()]
        if match:
            # filter on time > now
            match = [i for i in match if i.start_time > datetime.now().time()]
            # sort by time
            if match:
                match.sort(key=lambda x: x.start_time.strftime('%H:%M'))  # sort by time increasing
                return match[0]
          # take first in double sorted by day and time on next day or more
        match = [i for i in self if i.day_num > datetime.today().weekday()]
        if match:
            match.sort(key=lambda x: (x.day_num, x.start_time.strftime('%H:%M')))
            return match[0]
        # near end of week: take first next week
        match = self.sort(key=lambda x: (x.day_num, x.start_time.strftime('%H:%M')))
        if match:
            return match[0]
        return "No schedule items"

    def get_prev_entry():
        pass


test_mode = 0
if test_mode:
    # sys_config = SystemConfig()
    # print (sys_config)

    mysched = Schedule()
    days = [1, 3, 5]
    mytime1 = time(7, 30)
    mytime2 = time(19, 30)
    times = [mytime1, mytime2]
    mysched.add_entries(days, times, 20)
    print(mysched.get_next_entry())
    mysched.clear_entries()
    print(mysched.get_next_entry())

    


    # mysched = [i for i in mysched if i.day_num >= datetime.today().weekday()]  # keep days >= today
    # mysched.sort(key=lambda x: (x.day_num, x.start_time.strftime('%H:%M')))  # sort by day increasing
    

    # mysched.sort(key=lambda x: (x.day_num, x.start_time.strftime('%H:%M')))

    # j2 = [i for i in mysched if i.start_time > datetime.now().time()]
   


    # print(j2[-1])

    pass
