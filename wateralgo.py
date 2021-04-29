#!/usr/bin/python3

from crontab import CronTab


def water_scheduler(zone, duration, day, hour_time, minute_time):
    schedule = CronTab(user=True)
    command_string = './zone_control.py ' + zone + ' ' + str(duration)
    job = schedule.new(command=command_string, comment=‘SillySprinkler’)
    job.dow.on(day) # day must be three letter string, all caps
    job.minute.on(minute_time)
    job.hour.on(hour_time)
    schedule.write()