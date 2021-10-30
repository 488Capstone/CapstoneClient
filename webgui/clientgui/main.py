import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import os
from crontab import CronTab
from cron_descriptor import get_description
from werkzeug.exceptions import abort
from clientgui.db import get_db
from clientgui.auth import login_required
from sqlalchemy import text, exc
import capstoneclient.zone_control_defs as zc

bp = Blueprint('main', __name__)

#bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/home', methods=('GET', 'POST'))
@login_required
def home ():
    clientDir = os.getenv('SIOclientDir')
    if request.method == 'POST':
        if request.form.get('Toggle Zone1') == 'Toggle Zone1':
            # pass
            #print("Toggle Zone1 Valve!!!")
            zc.toggle_valve(1)
        elif  request.form.get('Open Zone1') == 'Open Zone1':
            if clientDir is None:
                zc.open_valve(1)
            else:
                os.system(f"cd {clientDir}; ./runPy.sh ./zone_control.py z1 0 on")
        elif  request.form.get('Close Zone1') == 'Close Zone1':
            if clientDir is None:
                zc.close_valve(1)
            else:
                os.system(f"cd {clientDir}; ./runPy.sh ./zone_control.py z1 0 off")
        elif  request.form.get('Enable WaterDemo') == 'Enable WaterDemo':
            if clientDir is not None:
                os.system(f"cd {clientDir}; ./runPy.sh ./capstoneclient/demo.py")
        elif  request.form.get('Disable WaterDemo') == 'Disable WaterDemo':
            import capstoneclient.demo as demo
            demo.disable_demo_water_mode()
#            if clientDir is not None:
#                os.system(f"cd {clientDir}; ./runPy.sh ./capstoneclient/demo.py")
        else:
            # pass # unknown
            pass
    #cronsched = my_cronschedule()
    cronsched = CronTab(user=True)
    db = get_db()
    systemInfo = {}
    with db.engine.connect() as conn:
        paramList = ["zipcode", "city", "state", "lat", "long", "soil_type", "plant_type", "microclimate", "slope", "pref_time_hrs", "pref_time_min", "application_rate", "water_deficit", "setup_complete"]
        for param in paramList:
            #print(param)
            systemInfo[param] = conn.execute(text('SELECT {} FROM system_configuration'.format(param))).fetchone()[0]

    return render_template('home.html', cronsched=cronsched, systemInfo=systemInfo)


def my_cronschedule():
    # TECHNICAL DEBT! This code is not hardened against all possible inputs.
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    
    #return_str = "Zone 1 is currently scheduled to run on \n" + str(schedule)
    return_str = str(schedule)
  #  for x in range(len(days)):
  #      return_str = return_str + "\nOn {}, zone 1 will run for {} minutes starting at {}:{}.".format(days[x][0], days[x][3], days[x][2], days[x][1]))
    return str(return_str)



