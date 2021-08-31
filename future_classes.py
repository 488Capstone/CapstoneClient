import threading

# An EnergyManager monitors sensors related to the battery and solar energy systems, controls switching from
#   grid to solar fed battery charging and switching control power from grid to battery
#   Saves history and reports useful information
class EnergyManager:
    def __init__(self):
        pass


# A UIManager responds to UI requests - json shadows?
class UIManager:
    def __init__(self):
        pass


# for logging historical events (system on/off, errors, schedule changes)
class EventManager:
    def __init__(self):
        pass


# handles schedule modifications - possibilities: default from zip/season, change by user request,
# percent adjust/water budget test, calibration, etc
class ScheduleManager:
    def __init__(self):
        pass


# handles sensors, respond with a datapoint, periods of data, etc
class SensorManager:
    def __init__(self):
        pass


class ThreadInstance(threading.Thread):
    def __init__(self, thread_id, name, counter):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.counter = counter

    def run(self):
        pass  # do things here. things start when start() called on a_thread [ThreadInstance]
    # => thread1 = ThreadInstance(1, "Thread1", 1), thread2 = ThreadInstance(2, "Thread2", 2)
    # => thread1.start(), thread2.start() <- calls run(). Thread dies when code finished
