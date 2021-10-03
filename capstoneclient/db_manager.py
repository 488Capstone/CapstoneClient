from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
# dont know why i have to add capstoneclient below.. same dir but this clears error
from capstoneclient.models import Base, SystemConfig, ZoneConfig, SensorEntry, HistoryItem
import os

import datetime

from capstoneclient.models import HistoryItem


class DBManager:



    def __init__(self):
        clientDir = os.getenv('SIOclientDir')
        if clientDir is not None:
            dbFileName = "sqlite+pysqlite:///{}/my_data".format(clientDir)
            #print("Creating database at path: " + dbFileName)
            self.engine = create_engine(dbFileName, echo=False, future=True)
            self.my_session = Session(self.engine)
            # self.Session = sessionmaker(self.engine)
            # self.start_databases()
        else:
            print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")
    # @property
    # def my_sys(self): 
    #     return self.get(SystemConfig, "system")
    # @property
    # def zone1(self): 
    #     return self.get(ZoneConfig, "zone1")
    # @property  
    # def zone2(self): 
    #     return self.get(ZoneConfig, "zone2")
    # @property
    # def zone3(self): 
    #     return self.get(ZoneConfig, "zone3")
    # @property
    # def zone4(self): 
    #     return self.get(ZoneConfig, "zone4")
    # @property
    # def zone5(self): 
    #     return self.get(ZoneConfig, "zone5")
    # @property
    # def zone6(self): 
    #     return self.get(ZoneConfig, "zone6")
    # @property
    # def zone_list(self): 
    #     return [self.zone1, self.zone2, self.zone3, self.zone4, self.zone5, self.zone6]
    
    
    
    
    def start_databases(self):
        """ Initializes database from models, creates tables if not present."""
        Base.metadata.create_all(self.engine)
        if not self.get(SystemConfig, "system"):
            self.setup_system()

    def close(self):
        self.my_session.close()
        self.engine.dispose()

    def add(self, obj):
        """ Adds an object to the correct table - defined by model."""
        self.my_session.add(obj)
        self.my_session.commit()
    
    def commit(self):
        self.my_session.commit

    def get(self, classname, key):
        """ Gets an object from the correct table - defined by model."""
        return self.my_session.get(classname, key)

    def setup_system(self):
        """Creates system and zones in db"""
        new_system = SystemConfig(id="system", setup_complete=False)
        new_system.zones_enabled = [1]
        self.add(new_system)
        num_zones = 6
        for r in range(num_zones):
            zone_id = "zone"+str(r+1)
            if not self.get(ZoneConfig, zone_id):
                new_zone = ZoneConfig(id = zone_id)
                new_zone.is_manual_mode = False
                self.add(new_zone)
        self.my_session.commit()
        
    
    def get_previous_week_water_deficit(self):
        one_week_ago_dt = datetime.date.today() - datetime.timedelta(days = 7)
        one_week_ago_date = one_week_ago_dt.date()
        result = self.my_session.query(HistoryItem).filter(HistoryItem.date >= one_week_ago_date)
        w_d = 0
        for row in result:
            print(f"db_manager.get_previous_week... water deficit for day {row.date} is {row.water_deficit}")
            w_d += row.water_deficit
        print(f"last week water deficit is {w_d}")
        return w_d
    
    def get_solar_for_date(self, date: datetime.date) -> float:
        query = self.my_session.query(HistoryItem).filter(HistoryItem.date == date)
        result = query.one_or_none()
        # result = self.get(HistoryItem, date)
        return result.solar

    def apply_solar_to_dates(self, tuple_list):
        for tup in tuple_list:
            item = self.my_session.query(HistoryItem).filter(HistoryItem.date == tup[0])
            item.solar = tup[1]
        self.my_session.commit()

    

# use/test:
# from datetime import datetime
# my_db = DBManager()
# my_db.start_databases()
# now_dt = datetime.now()
# new_sensor_entry = SensorEntry(datetime=now_dt, temp_c=37.2, pressure_hPa=5., moisture=57.8)
# my_db.add(new_sensor_entry)
# entry = my_db.get(SensorEntry, now_dt)
# entry.moisture = 1
# entry = my_db.get(SensorEntry, now_dt)
# # my_db.my_session.commit()
# my_db.add(entry)
#
# # now_dt2 = datetime.now()
# # new_sensor_entry2 = SensorEntry(datetime=now_dt2, temp_c=37.2, pressure_hPa=5., moisture=57.8)
# # my_db.add(new_sensor_entry2)
#
# print(entry)
# my_new_db = DBManager()
# new_entry = my_new_db.get(SensorEntry, now_dt)
# print(new_entry)
