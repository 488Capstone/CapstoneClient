import json
import sqlite3 as sl

# Initializes database
db = sl.connect('my-data.db')
# Creates table for weather history
db.execute("""
    CREATE TABLE IF NOT EXISTS HISTORY (
    date TEXT UNIQUE NOT NULL PRIMARY KEY,
    windspeed REAL,
    solar REAL,
    tmax REAL,
    tmin REAL,
    rh REAL,
    pressure REAL
    );
""")
db.commit()



# opens solar data file
with open('data/solardata.json') as f:
    data = json.load(f)

dailydata = []
temp = []

for x in data['estimated_actuals']:
    date = x['period_end'][0:10].replace('-', '')
    entry = [date, x['ghi']]
    temp.append(entry)

ghi = temp[0][1]
entrycounter = 1

for x in range(len(temp)):
    try:
        if x == (len(temp)-1):
            entry = [temp[x][0], (ghi / entrycounter)*86.4e-3] # converts ghi into MJ / (day * m^2) for ET calcs
            dailydata.append(entry)
        elif temp[x][0] == temp[x+1][0]:
            ghi += temp[x+1][1]
            entrycounter += 1
        else:
            entry = [temp[x][0], (ghi / entrycounter)*86.4e-3] # converts ghi into MJ / (day * m^2) for ET calcs
            dailydata.append(entry)
            ghi = temp[x][1]
            entrycounter = 1
    except:
        print("Exception occurred")
        pass

for x in range(len(dailydata)):
    cursor = db.cursor()
    cursor.execute("UPDATE HISTORY SET solar = ? WHERE date = ?", (dailydata[x][1], dailydata[x][0]))
    print(dailydata[x])
    print(type(dailydata[x][1]))
db.commit()
