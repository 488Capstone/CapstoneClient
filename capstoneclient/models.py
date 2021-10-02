from datetime import datetime, time, timedelta
import calendar
from typing import List

from sqlalchemy import Column, Boolean, Integer, Float, String, DateTime, Date, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import Enum, PickleType


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
    windspeed = Column(Float)  # wind - meters per second
    solar = Column(Float)  # shortwave solar radiation in  MJ / (m^2 * d)
    tmax = Column(Float)  # daily max temp in Celsius
    tmin = Column(Float)  # daily min temp in Celsius
    rh = Column(Float)  # daily average relative humidity
    pressure = Column(Float)
    precip = Column(Float)
    etcalc = Column(Float)
    water_deficit = Column(Float)


    def calculate_et_and_water_deficit(self) -> null: 
        """Call to generate and populate calculated values for History Item"""
        # todo: check these have reasonable values    
        # stretch: account for longwave solar radiation
         
        rh_decimal = self.rh / 100  # daily average relative humidity as a decimal
        pressure = self.pressure / 10  # database stores hectopascals (hPa), ET calc needs kilopascals (kPa)
        T = (self.tmax + self.tmin) / 2  # daily mean air temp in Celsius:
        G = 0  # from ASCE, G << R_n so G can be neglected. This can be improved later if desirable.
        e_omean = 0.6108 ** ((17.27 * T) / (T + 237.3))
        e_omin = 0.6108 ** ((17.27 * self.tmin) / (self.tmin + 237.3))
        e_omax = 0.6108 ** ((17.27 * self.tmax) / (self.tmax + 237.3))
        e_s = (e_omin + e_omax) / 2
        e_a = rh_decimal * e_omean
        delta = (2503 ** ((17.27 * T) / (T + 237.3))) / ((T + 237.3) ** 2)
        psycho = 0.000665 * pressure  # from ASCE standardized reference
        C_n = 900  # constant from ASCE standardized reference
        C_d = 0.34  # constant from ASCE standardized reference
        temp_solar = 1
        if self.solar is not None:
            #print("solar data was None. Setting to 1 to bypass issue")
            temp_solar = self.solar
        et_num = 0.408 * delta * (self.solar - G) + psycho * (C_n / (T + 273)) * self.windspeed * (e_s - e_a)
        et_den = delta + psycho * (1 + C_d * self.windspeed)

        etmm = et_num / et_den  # millimeters per day
        et = etmm / 25.4  # inches per day
        self.etcalc = et
        self.water_deficit = self.et - self.precip

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
    zones_enabled = Column(PickleType)

    def __repr__(self):
        return f"<System Config: \n" \
               f"zipcode={self.zipcode}, \n" \
               f"city={self.city}, \n" \
               f"state = {self.state}, \n" \
               f"latitude = {self.lat}, \n" \
               f"longitude = {self.long}, \n" \
               f"setup complete = {self.setup_complete}, \n" \
               f"water_deficit = {self.water_deficit}, \n" \
               f"zones_enabled = {self.zones_enabled} >"

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
    manual_schedule = Column(PickleType)
    scheduleString = Column(String)
    is_manual_mode = Column(Boolean)


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

    pass
