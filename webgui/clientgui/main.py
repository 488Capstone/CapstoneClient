import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from crontab import CronTab
from cron_descriptor import get_description
from werkzeug.exceptions import abort
from clientgui.db import get_db
from clientgui.auth import login_required

bp = Blueprint('main', __name__)

#bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/home')
@login_required
def home ():
    cronsched = my_cronschedule()
    return render_template('home.html', cronsched=cronsched)

def my_cronschedule():
    # TECHNICAL DEBT! This code is not hardened against all possible inputs.
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    days = [] # init empty array
    
    # dump every ZoneControl task into days array:
    for tasks in schedule:
        if tasks.comment == zone_control_comment_name:
            days.append([str(tasks[4]), str(tasks[0]), str(tasks[1]), str(tasks.command[23:26])])                      #
                                                                                                                       #
    # parse days array into usable strings:
    day_string = ""
    for x in range(len(days)):
        if days[x][0] == "MON": days[x][0] = "Monday"
        elif days[x][0] == "TUE": days[x][0] = "Tuesday"
        elif days[x][0] == "WED": days[x][0] = "Wednesday"
        elif days[x][0] == "THU": days[x][0] = "Thursday"
        elif days[x][0] == "FRI": days[x][0] = "Friday"
        elif days[x][0] == "SAT": days[x][0] = "Saturday"
        elif days[x][0] == "SUN": days[x][0] = "Sunday"

        if days[x][1] == "0": days[x][1] = "00"

        if int(days[x][2]) < 12: days[x][1] = days[x][1] + "AM"
        else: days[x][1] = days[x][1] + "PM"

        if x+1 == len(days):
            day_string = day_string + "and " + days[x][0]
        else:
            day_string = day_string + days[x][0] + ", "
    return_str = "Zone 1 is currently scheduled to run on {}." .format(day_string)
  #  for x in range(len(days)):
  #      return_str = return_str + "\nOn {}, zone 1 will run for {} minutes starting at {}:{}.".format(days[x][0], days[x][3], days[x][2], days[x][1]))
    return str(return_str)



