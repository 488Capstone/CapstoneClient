import datetime
import json
import sqlite3 as sl

# Initializes database
db = sl.connect('my-data.db')
# Creates table for weather history
db.execute("""
    CREATE TABLE IF NOT EXISTS HISTORY (
    date TEXT NOT NULL PRIMARY KEY,
    windspeed REAL,
    solarGHI REAL,
    tmax REAL,
    tmin REAL,
    rh REAL,
    pressure REAL
    );
""")
db.commit()

# opens weather history file
with open('data/weatherhistory.json') as f:
    data = json.load(f)

temp = []
dailydata = []  # this will hold the week's worth of valid data at the end.

for x in data['list']:
    timestamp = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d%H')
    date = datetime.datetime.fromtimestamp(int(x['dt'])).strftime('%Y%m%d')
    windspeed = x['wind']['speed']
    pressure = x['main']['pressure']
    humidity = x['main']['humidity']
    temp_min = x['main']['temp_min']
    temp_max = x['main']['temp_max']
    entry = [[timestamp], [date], [windspeed], [pressure], [humidity], [temp_min], [temp_max]]
    temp.append(entry)
    # print(entry)

# combines hourly data into min/max or avg daily values
avgwind = float(temp[0][2][0])
avgpres = float(temp[0][3][0])
avghum = float(temp[0][4][0])
temp_min = float(temp[0][5][0])
temp_max = float(temp[0][6][0])
entrycounter = 1

for x in range(len(temp)):
    try:
        if x == (len(temp)-1):
            entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter, (temp_min-273.15)*1.8+32, (temp_max-273.15)*1.8+32]
            dailydata.append(entry)
        elif temp[x][1] == temp[x+1][1]:
            entrycounter += 1
            avgwind += float(temp[x+1][2][0])
            avgpres += float(temp[x+1][3][0])
            avghum += float(temp[x+1][4][0])
            temp_min = min(temp_min, float(temp[x][5][0]), float(temp[x+1][5][0]))
            temp_max = max(temp_max, float(temp[x][6][0]), float(temp[x+1][6][0]))
        else:
            entry = [temp[x][1][0], avgwind / entrycounter, avgpres / entrycounter, avghum / entrycounter,
                     (temp_min - 273.15) * 1.8 + 32, (temp_max - 273.15) * 1.8 + 32]
            dailydata.append(entry)
            avgwind = float(temp[x+1][2][0])
            avgpres = float(temp[x+1][3][0])
            avghum = float(temp[x+1][4][0])
            temp_min = float(temp[x+1][5][0])
            temp_max = float(temp[x+1][6][0])
            entrycounter = 1

    except:
        print("Exception occurred")
        pass


# makes entries into HISTORY table of database
for x in range(len(dailydata)):
    #print(dailydata[x][1][0])
    cursor = db.cursor()
    cursor.execute('''INSERT OR IGNORE INTO HISTORY(date, windspeed, pressure, rh, tmin, tmax) VALUES(?,?,?,?,?,?)''', (dailydata[x][0], dailydata[x][1], dailydata[x][2], dailydata[x][3], dailydata[x][4], dailydata[x][5]))
    print("made commit")
    db.commit()

cursor = db.cursor()
cursor.execute('''SELECT * FROM HISTORY''')
all_rows = cursor.fetchall()
print(len(all_rows))
for row in all_rows:
    # row[0] returns the first column in the query (name), row[1] returns email column.
    print("row: ",row[0])

