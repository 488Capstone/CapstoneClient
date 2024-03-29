# DW 2021-10-14-20:02 Made this file since all of the cronjob cmd's need to have similar format to work.
#   Also, I need access to these crontab schedulers outside of the CLI menu, so I can call them from other scripts

import os
from crontab import CronTab
import getpass as gp
#import cron_descriptor as cd #get_description

DWDBG = False

ZONE_CONTROL_COMMENT_NAME = 'SIO-ZoneControl'
STARTUP_COMMENT_NAME = 'SIO-StartUp'
SENSORS_COMMENT_NAME = "SIO-Sensors"
DAILY_COMMENT_NAME = "SIO-Daily"
LOGFILE_COMMENT_NAME = "SIO-LogFileReset"

LOG_FILE_NAME = './client_dev.log'
#################################################
#    schedules watering events using crontab    #
#################################################
def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):
    pass
    #clientDir = os.getenv('SIOclientDir')
    #if checkClientDir() and checkUser():
    #    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    #    commentText = ZONE_CONTROL_COMMENT_NAME  
    #    schedule.remove_all(comment=commentText)
    #    #DW this var allows us to test the real schedule setting if we're in dev mode, if it remains 0 then we're in an accerated developer test mode
    #    #DW while we're still developing I guess it'll be nice to have the valve opening and closing at a faster rate
    #    setRealSched = False
    #    #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
    #    prescriptCmd = "cd {}; ./runPy.sh ".format(clientDir)
    #    #if on_raspi:
    #    command_string = "{} ./zone_control.py z{} " .format(prescriptCmd, str(zoneid))  #, LOG_FILE_NAME)   adds args to zone_control.py
    #    #else:
    #        #command_string = "{} ./zone_control_devmode.py {} {} " .format(prescriptCmd, str(zoneid), str(duration)) #  , LOG_FILE_NAME)  # adds args to zone_control.py
    #    
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


#example
#cron = CronTab(user='pi')
#task = cron[4]
#timeval = task.slices.render()
#cj.remove_cron_job(timeval, task.command)
#
def remove_cron_job(time, cmd):
    cron = CronTab(user='pi')  # opens the crontab (list of all tasks)
    iterator = cron.find_time(time)
    for item in iterator:
        if item.command == cmd:
            cron.remove(item)
    cron.write()

#DW expects a num for zonenum, list like ['MON','TUES'] for dow, and 24 hour time type integers for the rest
#cj.create_zone_event(1, ['SUN','TUE','THU'], 13, 30, 14, 35)
#cj.create_zone_event(1, ['SAT','SUN','TUE','THU'], 14, 21, 14, 22)
def create_zone_event(zonenum, dow, start_hr, start_min, end_hr, end_min):
    clientDir = os.getenv('SIOclientDir')
    if checkClientDir() and checkUser():
        # if day of week is only one day, then put it into a list so we can unpack it to the cron dow func
        if not isinstance(dow, list):
            dow = [dow]
        schedule = CronTab(user='pi')  # opens the crontab (list of all tasks)
        commentText = ZONE_CONTROL_COMMENT_NAME  
        #schedule.remove_all(comment=commentText)
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd {}; ./runPy.sh ".format(clientDir)
        command_string = "{} ./zone_control.py z{} " .format(prescriptCmd, str(zonenum))  #, LOG_FILE_NAME)   adds args to zone_control.py
        #DW TODO end hour time cannot be smaller than start time.

        #DW below will turn zone1 on
        # ./runPy.sh ./zone_control.py z1 0 on
        #DW below will turn zone1 off
        # ./runPy.sh ./zone_control.py z1 0 off

        ##############################################
        # ZONE ON
        ##############################################
        # adding three terms: second tells zone to go on or off, 1st tells zone it is a timed watering,
        # wait for off signal. Can set other than 0 for a short duration (raspi inside this script for duration)
        new_command_string = command_string+f"0 on"
        task = schedule.new(command=new_command_string, comment=commentText)  # creates a new entry in the crontab
        #unpack dow list so that it shows up as multiple args to dow.on func
        task.dow.on(*dow)  # day of week as per object passed to the method
        task.minute.on(int(start_min))  # minute-hand as per object passed to the method
        task.hour.on(int(start_hr))  # hour-hand as per object passed to the method

        ##############################################
        # ZONE OFF
        ##############################################
        new_command_string = command_string + f"0 off"
        task = schedule.new(command=new_command_string, comment=commentText)  # creates a new entry in the crontab
        #unpack dow list so that it shows up as multiple args to dow.on func
        task.dow.on(*dow)  # day of week as per object passed to the method
        task.minute.on(int(end_min))  # minute-hand as per object passed to the method
        task.hour.on(int(end_hr))  # hour-hand as per object passed to the method        schedule.write()  # finalizes the task in the crontab
        #print("task {} created" .format(x))
        schedule.write() # saves the changes to system crontab

def clear_zone_control():
    #schedule = CronTab(user='pi')  # opens the crontab (list of all tasks)
    #DW consider using user='pi'
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    result = schedule.remove_all(comment=ZONE_CONTROL_COMMENT_NAME)
    print(f"schedule.remove_all(comment={ZONE_CONTROL_COMMENT_NAME}) => {result}")
    schedule.write() # saves the changes to system crontab

def create_static_system_crons():
    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    clientDir = os.getenv('SIOclientDir')
    if checkClientDir() and checkUser():
        #DW 2021-09-20-08:29 prescriptCmd is expected to run before the cron job executed scripts, it will set the env var that
        #   tells subsequent scripts/programs what the location of the client side code is
        prescriptCmd = "cd {}; ".format(clientDir)
        commentText = LOGFILE_COMMENT_NAME
        schedule.remove_all(comment=commentText)
        log_update = schedule.new(command="{0} mv -v {1} {1}_last >> {1} 2>&1".format(prescriptCmd, LOG_FILE_NAME),
                                  comment=commentText)
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd += "./runPy.sh "
        commentText = DAILY_COMMENT_NAME
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
        commentText = SENSORS_COMMENT_NAME
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
    return


def create_cron_job(cmdstr, schedstr, commentText, rm_old=True):
    clientDir = os.getenv('SIOclientDir')
    if checkClientDir() and checkUser():
        schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
        if rm_old:
            schedule.remove_all(comment=commentText)
        #DW 2021-09-21-20:58 env/bin/python3 is necessary so that our subscripts have the python modules like crontab installed
        prescriptCmd = "cd {}; ".format(clientDir)
        command_string = "{} {} " .format(prescriptCmd, cmdstr)  
        task = schedule.new(command=command_string, comment=commentText)  # creates a new entry in the crontab
        task.setall(schedstr) 
        schedule.write()  # finalizes the task in the crontab

def create_startup_cron ():
    create_cron_job(' ./runStartUp.sh', '@reboot', STARTUP_COMMENT_NAME)

def checkUser ():
    username = gp.getuser()
    if username == 'pi':  
        return True
    else:
        print(f"username should be 'pi' to install crontabs, username: {username}")
        return False

def checkClientDir ():
    if os.getenv('SIOclientDir') is not None:
        return True
    else:
        print("env var 'SIOclientDir' must be set in shell to run cron jobs\n\tbash example: export SIOclientDir=/home/pi/capstoneProj/fromGit/CapstoneClient")
        return False

def get_cron_sched_for_webgui(filterList=None):
    if isinstance(filterList, str):
        filterList = [filterList]

    schedule = CronTab(user=True)  # opens the crontab (list of all tasks)
    descript = {
            ZONE_CONTROL_COMMENT_NAME: "Turns on/off a zone valve in the system",
            STARTUP_COMMENT_NAME: "Sets the starting state of the GPIO's and ensures cronjobs are defined",
            SENSORS_COMMENT_NAME: "Queries numerical samples from all of the sensors",
            DAILY_COMMENT_NAME: "Pulls in new weather data from the internet",
            LOGFILE_COMMENT_NAME: "Starts a new logfile so the logs don't grow indefinitely"
            }
    task_list = []
    for task in schedule:
        if filterList is None or (task.comment in filterList):
            #this should return only the timing specification for the task
            task_cron_sched = task.slices.render()
            #DW @reboot is apparently unsupported by cron_descriptor
            if task_cron_sched == "@reboot":
                timeval = "At Reboot"
            else:
                timeval = task.description(use_24hour_time_format=True)

            task_list.append({
                'comment':task.comment,
                'command':task.command,
                'time':timeval,
                'info':DWget(descript, task.comment, "")
                }
            )
    return task_list

def DWprintSched():
    print(get_cron_sched_for_webgui())

def DWget(dic, key, defval):
    if key not in dic.keys():
        return defval
    else:
        return dic[key]

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


