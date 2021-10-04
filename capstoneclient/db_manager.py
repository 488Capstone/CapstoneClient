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
            self.engine = create_engine(dbFileName, echo=False, future=True)
            self.my_session = Session(self.engine)

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
    
    def commit(self):
        self.my_session.commit()

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
        one_week_ago_date = datetime.date.today() - datetime.timedelta(days = 7)
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
        return result.solar

    def apply_solar_to_dates(self, tuple_list):
        for tup in tuple_list:
            item = self.my_session.query(HistoryItem).filter(HistoryItem.date == tup[0])
            item.solar = tup[1]
        self.my_session.commit()

