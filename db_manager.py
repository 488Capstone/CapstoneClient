from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, SystemZoneConfig, SensorEntry, HistoryItem


class DBManager:

    def __init__(self):
        self.engine = create_engine("sqlite+pysqlite:///my_data", echo=True, future=True)
        self.my_session = Session(self.engine)
        # self.Session = sessionmaker(self.engine)

    def start_databases(self):
        """ Initializes database from models, creates tables if not present."""
        Base.metadata.create_all(self.engine)
        if not self.get(SystemZoneConfig, "system"):
            self.setup_system()

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
        new_system = SystemZoneConfig(id="system", setup_complete=False)
        self.add(new_system)
        # todo: num_zones to system db
        num_zones = 1
        for r in range(1):
            new_zone = SystemZoneConfig(id="zone"+str(r+1))
            self.add(new_zone)


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