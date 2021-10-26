# DW 2021-10-14-20:02 Made this file since all of the cronjob cmd's need to have similar format to work.
#   Also, I need access to these crontab schedulers outside of the CLI menu, so I can call them from other scripts

import os
from crontab import CronTab
# from cron_descriptor import get_description

DWDBG = False

ZONE_CONTROL_COMMENT_NAME = 'SIO-ZoneControl'
STARTUP_COMMENT_NAME = 'SIO-StartUp'
LOG_FILE_NAME = './client_dev.log'
#################################################
#    schedules watering events using crontab    #
#################################################
def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):
    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
        commentText = ZONE_CONTROL_COMMENT_NAME  
        schedule.remove_all(comment=commentText)
        #DW this var allows us to test the real schedule setting if we're in dev mode, if it remains 0 then we're in an accerated developer test mode
        #DW while we're still developing I guess it'll be nice to have the valve opening and closing at a faster rate
        setRealSched = False
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd {}; ./runPy.sh ".format(clientDir)
        #if on_raspi:
        command_string = "{} ./zone_control.py {} " .format(prescriptCmd, str(zoneid))  #, LOG_FILE_NAME)   adds args to zone_control.py
        #else:
            #command_string = "{} ./zone_control_devmode.py {} {} " .format(prescriptCmd, str(zoneid), str(duration)) #  , LOG_FILE_NAME)  # adds args to zone_control.py
        
#        if setRealSched:
#            for x in range(len(days)):
#                # NB: turning on for duration doesnt work well.. keeps raspi locked up for minutes/hours in
#                # zone_control.py.  best way to have cron run python every 15 min or so, python handles turning on/off
#                # during those times but for now: make two chron entries, one on and one off (after duration).. third
#                # value now on_off
#                # todo: fix finish time on next day
#
#                # adding three terms: second tells zone to go on or off, 1st tells zone it is a timed watering,
#                # wait for off signal. Can set other than 0 for a short duration (raspi inside this script for duration)
#                new_command_string = command_string+f"0 on {LOG_FILE_NAME}"
#                task = schedule.new(command=new_command_string,
#                                    comment=commentText)  # creates a new entry in the crontab
#                task.dow.on(days[x])  # day of week as per object passed to the method
#                task.minute.on(int(pref_time_min))  # minute-hand as per object passed to the method
#                task.hour.on(int(pref_time_hrs))  # hour-hand as per object passed to the method
#
#                schedule.write()  # finalizes the task in the crontab
#                print("task {} created".format(x))
#
#                new_command_string = command_string + f"0 off {LOG_FILE_NAME}"
#                task = schedule.new(command=new_command_string,
#                                    comment=commentText)  # creates a new entry in the crontab
#                task.dow.on(days[x])  # day of week as per object passed to the method
#                finish_minute = pref_time_min + duration
#                finish_hour = pref_time_hrs
#                if finish_minute > 59:
#                    finish_hour += finish_hour // 60
#                    finish_minute = finish_minute % 60
#
#                task.minute.on(int(finish_minute))  # minute-hand as per object passed to the method
#                task.hour.on(int(finish_hour))  # hour-hand as per object passed to the method
#
#                schedule.write()  # finalizes the task in the crontab
#                print("task {} created" .format(x))
#        else:
#            # use short duration function, 1 minute => no off chron
#            new_command_string = command_string + f"1 on {LOG_FILE_NAME}"
#            task = schedule.new(command=new_command_string, comment=commentText)  # creates a new entry in the crontab
#            task.setall('*/5 * * * *') # run every 5min
#            schedule.write()  # finalizes the task in the crontab
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")


def create_static_system_crons():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        #DW 2021-09-20-08:29 prescriptCmd is expected to run before the cron job executed scripts, it will set the env var that
        #   tells subsequent scripts/programs what the location of the client side code is
        prescriptCmd = "cd {}; ".format(clientDir)
        commentText = "SIO-LogFileReset"
        schedule.remove_all(comment=commentText)
        log_update = schedule.new(command="{0} mv -v {1} {1}_last >> {1} 2>&1".format(prescriptCmd, LOG_FILE_NAME),
                                  comment=commentText)
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd += "./runPy.sh "
        commentText = "SIO-Daily"
        schedule.remove_all(comment=commentText)
        daily_update = schedule.new(command=" {0} ./dailyactions.py dailyupdate ".format(prescriptCmd, LOG_FILE_NAME) , comment=commentText)
        if not DWDBG:
            #normal operation
            #every day at 3am
            daily_update.setall('0 3 * * *')
            #every 14 days at 3am?
            log_update.setall('0 3 */14 * *')
        else:
            #every 10min
            daily_update.setall('*/10 * * * *')
            log_update.setall('*/50 * * * *')

        #if on_raspi:
            #normal operation
        commentText = "SIO-Sensors"
        schedule.remove_all(comment=commentText)
        sensor_query = schedule.new(command="{0} ./dailyactions.py readsensors".format(prescriptCmd, LOG_FILE_NAME), comment=commentText)
        sensor_query.setall('*/5 * * * *')
       # else:
       #     commentText = "SIO-DEV"
       #     schedule.remove_all(comment=commentText)
       #     dev_mode = schedule.new(command="{0} ./dailyactions.py DEV".format(prescriptCmd, LOG_FILE_NAME), comment=commentText)
       #     # every 1 minute
       #     dev_mode.setall('*/1 * * * *')

        schedule.write()
        print(schedule)
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")
    return


def create_cron_job(cmdstr, schedstr, commentText, rm_old=True):
    clientDir = os.getenv('SIOclientDir')
    if clientDir is not None:
        schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
        if rm_old:
            schedule.remove_all(comment=commentText)
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd {}; ".format(clientDir)
        command_string = "{} {} " .format(prescriptCmd, cmdstr)  
        task = schedule.new(command=command_string, comment=commentText)  # creates a new entry in the crontab
        task.setall(schedstr) 
        schedule.write()  # finalizes the task in the crontab
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")

def create_startup_cron ():
        create_cron_job(' ./runStartUp.sh', '@reboot', STARTUP_COMMENT_NAME)

# my_schedule() displays basic scheduling data when requested from op_menu()
def my_schedule():
    # TECHNICAL DEBT! This code is not hardened against all possible inputs.
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    days = []  # init empty array

    # dump every ZoneControl task into days array:
    for tasks in schedule:
        if tasks.comment == ZONE_CONTROL_COMMENT_NAME:
            days.append([str(tasks[4]), str(tasks[0]), str(tasks[1]), str(tasks.command[23:26])])

    # parse days array into usable strings:
    day_string = ""
    for x in range(len(days)):
        if days[x][0] == "MON":
            days[x][0] = "Monday"
        elif days[x][0] == "TUE":
            days[x][0] = "Tuesday"
        elif days[x][0] == "WED":
            days[x][0] = "Wednesday"
        elif days[x][0] == "THU":
            days[x][0] = "Thursday"
        elif days[x][0] == "FRI":
            days[x][0] = "Friday"
        elif days[x][0] == "SAT":
            days[x][0] = "Saturday"
        elif days[x][0] == "SUN":
            days[x][0] = "Sunday"

        if days[x][1] == "0":
            days[x][1] = "00"

        if int(days[x][2]) < 12:
            days[x][1] = days[x][1] + "AM"
        else:
            days[x][1] = days[x][1] + "PM"

        if x+1 == len(days):
            day_string = day_string + "and " + days[x][0]
        else:
            day_string = day_string + days[x][0] + ", "
    print("Zone 1 is currently scheduled to run on {}." .format(day_string))
    for x in range(len(days)):
        print("On {}, zone 1 will run for {} minutes starting at {}:{}." \
              .format(days[x][0], days[x][3], days[x][2], days[x][1]))


