from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
# dont know why i have to add capstoneclient below.. same dir but this clears error
from capstoneclient.models import Base, SystemConfig, ZoneConfig, SensorEntry, HistoryItem
import os

import datetime

from models import HistoryItem


class DBManager:

    def __init__(self):
        clientDir = os.getenv('SIOclientDir')
        if clientDir is not None:
            dbFileName = "sqlite+pysqlite:///{}/my_data".format(clientDir)
            #print("Creating database at path: " + dbFileName)
            self.engine = create_engine(dbFileName, echo=False, future=True)
            self.my_session = Session(self.engine)
            # self.Session = sessionmaker(self.engine)
        else:
            print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")

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


    def get(self, classname, key):
        """ Gets an object from the correct table - defined by model."""
        # with self.Session() as session:
        #     return session.get(classname, key)
        return self.my_session.get(classname, key)

    def setup_system(self):
        new_system = SystemConfig(id="system", setup_complete=False)
        self.add(new_system)
        # todo: num_zones to system db
        num_zones = 1
        for r in range(1):
            new_zone = ZoneConfig(id="zone"+str(r+1))
            self.add(new_zone)
    
    def get_previous_week_water_deficit(self):
        one_week_ago = datetime.date(datetime.datetime.now() - datetime.timedelta(days = 7))
        result = self.my_session.query(HistoryItem).filter(HistoryItem.date)
        w_d = 0
        for row in result:
            w_d += row.water_deficit
        
        return w_d


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
