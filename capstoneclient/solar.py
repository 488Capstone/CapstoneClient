from typing import List
import requests
import json
from datetime import datetime, date

Nolan_key = "TjfO_sKLdS4JWxn5j8nKo1FTcC-t8yyI"
Collin_key = "N5x3La865UcWH67BIq3QczgKVSu8jNEJ"

def solar_radiation_for_dates(dates: list, lat: float, long: float) -> list:
    """Takes list of dates, returns list of (date,solar) tuples"""
    data = fetch_hour_data(lat, long) # one week of 30min data
    tuple_list = parsesolar(data)
    matched_tuple_list = []

    for tup in tuple_list:
        if tup[0] in dates:
            matched_tuple_list.append(tup)
    
    return matched_tuple_list

    
def fetch_hour_data(lat: float, long: float, hours:int = 168) -> json:
    """Gets hourly data. Limited to 10 calls per api key. """

    apikey, payload, headers = Collin_key, {}, {}
    url = f"https://api.solcast.com.au/world_radiation/estimated_actuals?api_key={apikey}&latitude={lat}&longitude={long}&hours={hours}&format=json"
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)

def fetch_forecast_data(lat: float, long: float, hours:int = 168) -> json:
    """Gets hourly data. Limited to 10 calls per api key. """

    apikey, payload, headers = Collin_key, {}, {}
    url = f"https://api.solcast.com.au/world_radiation/forecasts?api_key={apikey}&latitude={lat}&longitude={long}&hours={hours}&format=json"
    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)


def parsesolar(data: json) -> tuple:
    """From hourly solar api data returns a single daily total solar radiation in MJ/m2 for each date (date, float)."""

    # ghi_total = 0
    # for x in data['estimated_actuals']:
    #     ghi_total += x['ghi']  # W/m2 (mean of 30min)
    #     ave_ghi = ghi_total / len(data['estimated_actuals'])
    #     daily_solar_radiation = ave_ghi * 0.0864  # converts ghi into MJ / (day * m^2) per Collin # TODO: check this2


    dailydata = []
    temp = []


    for x in data['estimated_actuals']:
        # date = x['period_end'][0:10].replace('-', '')
        entry_date = datetime.fromisoformat(x['period_end'][:-2]).date()
        entry = [entry_date, x['ghi']]
        temp.append(entry)


    ghi = temp[0][1]
    entrycounter = 1

    for x in range(len(temp)):
        try:
            if x == (len(temp)-1): # last line => end of last day
                date_ghi_tuple = (temp[x][0], (ghi / entrycounter)*0.0864)  # converts ghi into MJ / (day * m^2)
                dailydata.append(date_ghi_tuple)
            elif temp[x][0] == temp[x+1][0]: # line date == next line
                ghi += temp[x+1][1]
                entrycounter += 1
            else:  # last line of day
                date_ghi_tuple = (temp[x][0], (ghi / entrycounter)*0.0864)  # converts ghi into MJ / (day * m^2)
                dailydata.append(date_ghi_tuple)
                ghi = temp[x][1]
                entrycounter = 1
        except:
            print("Exception occurred while parsing historical solar data.")
            pass

    return dailydata
# forecast_data = json.dumps(fetch_forecast_data(-33.856784, 151.215297))
# with open("data/solar_forecast_data.json", 'w') as f:
#         f.write(forecast_data)

   