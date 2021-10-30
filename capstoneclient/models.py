from sqlalchemy import Column, Boolean, Integer, Float, String, DateTime, Date, MetaData, JSON
from sqlalchemy.orm import declarative_base


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


#TODO DW I think these should ideally be two seperate things... but for now, w/e
# SYSTEM table holds data on both zones and the system as a whole. Some columns are only for zone/system data.
class SystemZoneConfig(Base):
    __tablename__ = "system_configuration"
    id = Column(String, primary_key=True)
    zipcode = Column(Integer)
    city = Column(String)
    state = Column(String)
    lat = Column(Float)
    long = Column(Float)
    soil_type = Column(String)
    plant_type = Column(String)
    microclimate = Column(String)
    slope = Column(Float)
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
    water_deficit = Column(Float)
    setup_complete = Column(Boolean)

class JsonTable(Base):
    __tablename__ = "json"
    # what is this Sequence("item_id_seq")? I don't know, I'm just following an example online
    id = Column(String, primary_key=True, nullable=False)
    json = Column(JSON, nullable = True)


