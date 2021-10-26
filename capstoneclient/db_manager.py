from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, SystemZoneConfig, SensorEntry, HistoryItem
import os


class DBManager:
    def __init__(self):
        clientDir = os.getenv('SIOclientDir')
        if clientDir is not None:
            #TODO DW 2021-10-26-11:48 safer to use os.path.join
            #DATABASE=os.path.join(clientDir, 'my_data'),
            dbFileName = f"sqlite+pysqlite:///{clientDir}/my_data"
            #print("Creating database at path: " + dbFileName)
            self.engine = create_engine(dbFileName, echo=False, future=True)
            self.my_session = Session(self.engine)
            # self.Session = sessionmaker(self.engine)
        else:
            print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")

    def start_databases(self):
        """ Initializes database from models, creates tables if not present."""
        Base.metadata.create_all(self.engine)
        if not self.get(SystemZoneConfig, "system"):
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
        new_system = SystemZoneConfig(id="system", setup_complete=False)
        self.add(new_system)
        # todo: num_zones to system db
        num_zones = 1
        for r in range(num_zones):
            new_zone = SystemZoneConfig(id="zone"+str(r+1))
            self.add(new_zone)
        self.set_db_initialvals(self)

    def set_db_initialvals(self):
        print('Database Initializing...')
        db = self
        my_sys = db.get(SystemZoneConfig, "system")
        zone1 = db.get(SystemZoneConfig, "zone1")
        import requests

        # Get location data from IP address:
        loc = requests.get('http://ipapi.co/json/?key=H02y7T8oxOo7CwMHhxvGDOP7JJqXArMPjdvMQ6XhA6X4aR4Tub').json()

        # enter location into system database:
        my_sys.city, my_sys.state, my_sys.zipcode, my_sys.lat, my_sys.long = \
            loc['city'], loc['region_code'], loc['postal'], loc['latitude'], loc['longitude']

        db.add(my_sys)  # add/update object

        print(f"We think you're in {my_sys.city}, {my_sys.state} {my_sys.zipcode}")
        print(f"Lat/long: {my_sys.lat}, {my_sys.long}")

        # get historical weather / solar data, build database.
        # This does the past week as a starting point for a water deficit.
        #TODO DW 2021-10-26-11:17 need to straighten out historical data
        #history_items_list = gethistoricaldata(days=7, latitude=my_sys.lat, longitude=my_sys.long)
        #print("Database of historical environmental data built.")

        # build system info:
        #print("Lets talk about Zone 1, since this is a limited prototype and all.")
        #soil_type = input("What is the predominant soil type in this zone? [limit answers to 'sandy' or ""'loamy']")
#        while soil_type != ("sandy" or "loamy"):
#            soil_type = input("Sorry, we didn't quite catch that...is the predominant soil type in this zone sandy or "
#                              "loamy?")
        soil_type = "sandy"
        zone1.soil_type = soil_type

        # TECHNICAL DEBT! improve user selection of watering days and times.
        if soil_type == 'sandy':
            print("Sandy soil doesn't hold water well; more frequent waterings are best to keep your plants healthy.")
            print("Three days a week should do nicely. Lets say Mon-Weds-Fri for now.")

            zone1.waterSun, zone1.waterMon, zone1.waterTue, zone1.waterWed, zone1.waterThu, zone1.waterFri, zone1.waterSat\
                = 0, 1, 0, 1, 0, 1, 0

        elif soil_type == 'loamy':
            print("Your loamy soil will hold water well. We recommend picking one watering day a week.")
            print("We'll make it easy and pick Wednesday for now.")
            zone1.waterSun, zone1.waterMon, zone1.waterTue, zone1.waterWed, zone1.waterThu, zone1.waterFri, zone1.waterSat \
                = 0, 0, 0, 1, 0, 0, 0

        # TECHNICAL DEBT! Prototype doesn't allow changing the time of day for watering.
        zone1.application_rate = 1.5
        zone1.pref_time_hrs = '09'
        zone1.pref_time_min = '00'

#        print("Okay, it looks like we have everything we need to calculate your water needs. We'll do that now.")
        waterdeficit = 1
#        for x in range(7):
#            waterdeficit += history_items_list[x].etcalc
#
#        print("Now to account for accumulated precipitation...")
#        for x in range(7):
#            waterdeficit -= history_items_list[x].precip
#
        zone1.water_deficit = waterdeficit
        db.add(zone1)  # add/update object
        print('Finished Database Initialization')



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
