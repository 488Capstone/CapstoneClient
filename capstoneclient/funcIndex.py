capstoneclient.py:def op_menu(): # op_menu() is the landing spot for operations.
    # user interface from command line
capstoneclient.py:def my_system(): # prints some system info (zip code/location, zone 1 info, application rate)
capstoneclient.py:def my_schedule(): #  displays basic scheduling data, pulls from the system CronTab settings
capstoneclient.py:def startup(): #setup sequence for first time starting
capstoneclient.py:def task_scheduler(): # adds dailyactions.py to system cron jobs
capstoneclient.py:def application_rate_cal(): #function to calibrate watering application amount of output sprinklers
capstoneclient.py:def raspi_testing(): # running on the raspi, menu interface
webgui/clientgui/auth.py:def register():
webgui/clientgui/auth.py:def login():
webgui/clientgui/auth.py:def load_logged_in_user():
webgui/clientgui/auth.py:def logout():
webgui/clientgui/auth.py:def login_required(view):
webgui/clientgui/auth.py:    def wrapped_view(**kwargs):
webgui/clientgui/main.py:def home ():
webgui/clientgui/__init__.py:def create_app(test_config=None):
webgui/clientgui/__init__.py:    def hello():
webgui/clientgui/__init__.py:    def first_page ():
webgui/clientgui/db.py:def init_app(app):
webgui/clientgui/db.py:def get_db():
webgui/clientgui/db.py:def close_db(e=None):
webgui/clientgui/db.py:def init_db():
webgui/clientgui/db.py:def init_db_command():
webgui/webgui_main.py:def webgui_main():
webgui/webgui_main.py:def DWtestfunc ():
db_manager.py:    def __init__(self):
db_manager.py:    def start_databases(self):
db_manager.py:    def add(self, obj):
db_manager.py:    def get(self, classname, key):
db_manager.py:    def setup_system(self):
cloud_controller.py:def on_connect(client, userdata, flags, rc):
cloud_controller.py:def on_message(client, userdata, msg):
cloud_controller.py:def get_device_shadow():
publish.py:def customShadowCallback_Update(payload, responseStatus, token):
publish.py:def customShadowCallback_Delete(payload, responseStatus, token):
publish.py:def configureLogging():
publish.py:def publish(payload):
publish.py:def parseArgs():
dailyactions.py:def baro(): #handle pressure reading
dailyactions.py:def soil(): #handle moisture reading
dailyactions.py:def adc(): # currently working in adcsource.py
dailyactions.py:def gethistoricaldata(days: int = 1, latitude: float = 0., longitude=0.) -> list[HistoryItem]:
dailyactions.py:    def getsolar(lat_s, long_s):  # pulls solar data
dailyactions.py:    def getweather(lat_w, long_w):
dailyactions.py:    def parseweather(lat_pw, long_pw) -> list[HistoryItem]:  # parses weather data pulled from getweather()
dailyactions.py:    def parsesolar(lat_ps: float, long_ps: float, wl: list[HistoryItem]) -> list[HistoryItem]:
dailyactions.py:def et_calculations(h_i: HistoryItem) -> HistoryItem:  # string passed determines what day ET is evaluated for
dailyactions.py:def water_algo(zone: SystemZoneConfig) -> float:
dailyactions.py:def water_scheduler(zoneid, days, duration, pref_time_hrs, pref_time_min):
models.py:    def __repr__(self):
models.py:    def __repr__(self):
raspispecific.py:def manual_control():
adcsource.py:    def __init__(self, address=0x48, ic=__IC_ADS1015, debug=False):
adcsource.py:    def readADCSingleEnded(self, channel=0, pga=6144, sps=250):
adcsource.py:    def readADCDifferential(self, chP=0, chN=1, pga=6144, sps=250):
adcsource.py:    def readADCDifferential01(self, pga=6144, sps=250):
adcsource.py:    def readADCDifferential03(self, pga=6144, sps=250):
adcsource.py:    def readADCDifferential13(self, pga=6144, sps=250):
adcsource.py:    def readADCDifferential23(self, pga=6144, sps=250):
adcsource.py:    def startContinuousConversion(self, channel=0, pga=6144, sps=250):
adcsource.py:    def startContinuousDifferentialConversion(self, chP=0, chN=1, pga=6144, sps=250):
adcsource.py:    def stopContinuousConversion(self):
adcsource.py:    def getLastConversionResults(self):
adcsource.py:    def startSingleEndedComparator(self, channel, thresholdHigh, thresholdLow, \
adcsource.py:    def startDifferentialComparator(self, chP, chN, thresholdHigh, thresholdLow, \
From:
~/.local/lib/python3.7/site-packages/cron_descriptor/ExpressionDescriptor.py
def get_description(self, description_type=DescriptionTypeEnum.FULL):
    """Generates a human readable string for the Cron Expression

    Args:
        description_type: Which part(s) of the expression to describe
    Returns:
        The cron expression description
    Raises:
        Exception: if throw_exception_on_parse_error is True

    """

def get_full_description(self):
    """Generates the FULL description

    Returns:
        The FULL description
    Raises:
        FormatException: if formating fails and throw_exception_on_parse_error is True

    """
def get_time_of_day_description(self):
    """Generates a description for only the TIMEOFDAY portion of the expression

    Returns:
        The TIMEOFDAY description

    """
def get_seconds_description(self):
    """Generates a description for only the SECONDS portion of the expression

    Returns:
        The SECONDS description

    """
def get_minutes_description(self):
    """Generates a description for only the MINUTE portion of the expression

    Returns:
        The MINUTE description

    """
def get_hours_description(self):
    """Generates a description for only the HOUR portion of the expression

    Returns:
        The HOUR description

    """
def get_day_of_week_description(self):
    """Generates a description for only the DAYOFWEEK portion of the expression

    Returns:
        The DAYOFWEEK description

    """
def get_month_description(self):
    """Generates a description for only the MONTH portion of the expression

    Returns:
        The MONTH description

    """
       def get_day_of_month_description(self):
    """Generates a description for only the DAYOFMONTH portion of the expression

    Returns:
        The DAYOFMONTH description

    """
def get_year_description(self):
    """Generates a description for only the YEAR portion of the expression

    Returns:
        The YEAR description

    """
def get_segment_description(
    self,
    expression,
    all_description,
    get_single_item_description,
    get_interval_description_format,
    get_between_description_format,
    get_description_format
):
    """Returns segment description
    Args:
        expression: Segment to descript
        all_description: *
        get_single_item_description: 1
        get_interval_description_format: 1/2
        get_between_description_format: 1-2
        get_description_format: format get_single_item_description
    Returns:
        segment description

    """
def generate_between_segment_description(
        self,
        between_expression,
        get_between_description_format,
        get_single_item_description
):
    """
    Generates the between segment description
    :param between_expression:
    :param get_between_description_format:
    :param get_single_item_description:
    :return: The between segment description
    """
def format_time(
    self,
    hour_expression,
    minute_expression,
    second_expression=''
):
    """Given time parts, will contruct a formatted time description
    Args:
        hour_expression: Hours part
        minute_expression: Minutes part
        second_expression: Seconds part
    Returns:
        Formatted time description

    """
def transform_verbosity(self, description, use_verbose_format):
    """Transforms the verbosity of the expression description by stripping verbosity from original description
    Args:
        description: The description to transform
        use_verbose_format: If True, will leave description as it, if False, will strip verbose parts
        second_expression: Seconds part
    Returns:
        The transformed description with proper verbosity

    """
def get_description(expression, options=None):
    """Generates a human readable string for the Cron Expression
    Args:
        expression: The cron expression string
        options: Options to control the output description
    Returns:
        The cron expression description"""








