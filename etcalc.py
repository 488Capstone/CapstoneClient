import datetime
import sqlite3 as sl
import math
from datetime import date

# TODO: Calculate evapotranspiration
def et_calculations(date):  # string passed determines what day ET is evaluated for
    db = sl.connect('my-data.db')  # connect to database for historical data
    cursor = db.cursor()
    cursor.execute("select * from history where date = ?", (date,))
    dbdata = cursor.fetchone()
    wind = dbdata[1]  # wind - meters per second,
    # TODO: account for longwave solar radiation
    solar = dbdata[2]  # shortwave solar radiation in  MJ / (m^2 * d)
    T_max = dbdata[3]  # daily max temp in Celsius
    T_min = dbdata[4]  # daily min temp in Celsius
    rh = dbdata[5] / 100  # daily average relative humidity as a decimal
    pressure = dbdata[6] / 10  # database stores hectopascals (hPa), ET calc needs kilopascals (kPa)


    T = (T_max + T_min) / 2  # daily mean air temperature in Celsius

    G = 0  # from ASCE, G << R_n so G can be neglected. This can be improved later if desirable.

    e_omean = 0.6108 ** ((17.27 * T) / (T + 237.3))
    e_omin = 0.6108 ** ((17.27 * T_min) / (T_min + 237.3))
    e_omax = 0.6108 ** ((17.27 * T_max) / (T_max + 237.3))
    e_s = (e_omin + e_omax) / 2
    e_a = rh * e_omean

    delta = (2503 ** ((17.27 * T) / (T + 237.3))) / ((T + 237.3) ** 2)
    psycho = 0.000665 * pressure  # from ASCE standardized reference
    C_n = 900  # constant from ASCE standardized reference
    C_d = 0.34  # constant from ASCE standardized reference

    et_num = 0.408 * delta * (solar - G) + psycho * (C_n / (T + 273)) * wind * (e_s - e_a)
    et_den = delta + psycho * (1 + C_d * wind)

    etmm = et_num / et_den  # millimeters per day
    et = etmm / 25.4 # inches per day
    # TODO: log date, calculated ET, and environmental data to database.

    # enters calculated into HISTORY database
    cursor = db.cursor()
    cursor.execute("UPDATE HISTORY SET etcalc = ? WHERE date = ?", (et, date))
    db.commit()

    return et


def et_calculations_testing():
    et = 0.2
    return et

if __name__ == "__main__":
    et_calculations('20210506')
    et_calculations('20210505')
    et_calculations('20210504')
    et_calculations('20210503')
    et_calculations('20210502')
    et_calculations('20210501')
    today = date.today().strftime("%Y%m%d")
    print(today)
    date = (date.today() - datetime.timedelta(days=0)).strftime("%Y%m%d")
    print(date)