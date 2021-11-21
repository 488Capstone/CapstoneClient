
import time
import types #For the adc conversions
import math #DW natural log needed for temp eq
from datetime import timedelta, datetime

try:
    import smbus
    import busio
    import board
    from board import SCL, SDA
    from adafruit_seesaw.seesaw import Seesaw
    #for the ADC
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except Exception as e:
    print("Importing raspi Python libs failed")
    print(e)
    import traceback
    errMsg = traceback.format_exc()
    print(errMsg)


# TODOdone: Read ADC.
################################
#   ADC module functionality   #
################################
def read_adc(addr, pin):  # currently working in adcsource.py
    adc_value = 0
    adc_voltage = 0
    try:
        i2c_bus = board.I2C()
        adc = ADS.ADS1115(i2c_bus, address=addr)
        if pin == 0:
            channel = AnalogIn(adc, ADS.P0)
        elif pin == 1:
            channel = AnalogIn(adc, ADS.P1)
        elif pin == 2:
            channel = AnalogIn(adc, ADS.P2)
        elif pin == 3:
            channel = AnalogIn(adc, ADS.P3)
        else:
            channel = AnalogIn(adc, ADS.P0)
        adc_value = channel.value
        adc_voltage = channel.voltage
    except Exception as e:
        print(e)

    # print(f"Soil Moisture: {soilmoisture}, Soil Temp: {soiltemp}")
    return adc_value, adc_voltage

def vadc_to_temp(vadc):
    Vsupply = 3.3
    R1 = 4.99e3
    R0 = 10e3
    Rnew = (vadc*R1)/(Vsupply-vadc)
    B = 3380
    kelvin_shift = 273.15
    Tref = 25 + kelvin_shift
    Tnew = -1/(math.log(Rnew/R0)/(-B) - 1/Tref) - kelvin_shift
    return Tnew

def vadc_to_current(vadc):
    #currentGain equation is Vadc * 1/(4mA/V * Rsense * Rgain) = I_sense
    #DW 2021-10-03-14:47 I have a OneNote eq showing how to derive this
    currentGain = (1/(4e-3*8e-3*41.2e3))
    return currentGain*vadc

# DW function used as an internal wrapper around code that is the same between two branches of the read_adc_for function
def read_adc_for_internal (select, arglist, verbose=True):
    addr = arglist[0]
    pin = arglist[1]
    unit = arglist[2]
    if len(arglist) > 3:
        gain = arglist[3]
    else:
        gain = 1

    val, volt = read_adc(addr, pin)
    finalresult = volt
    if isinstance(gain, types.FunctionType):
        finalresult = gain(volt)
    elif isinstance(gain, (float, int)):
        finalresult = gain*volt #convert back to original magnitude before the sense ratio was applied
    if verbose:
        timenow = str(datetime.now())
        #print(f"{timenow}---{select}: ADC(0x{addr:02x})-PIN({pin}):: value: {val}, voltage: {volt}")
        print(f"{timenow}---{select}: {finalresult} {unit}")
    return finalresult

# DW This function is a convenience wrapper around the read_adc. You use the pin/net name from the schematic of our PC board 
#   to tell it what value to read/return!
    #DW 2021-09-29-20:12 if 'all' is selected, loop through all options and return a dict instead of a single atom value
    # if 'all' is not selected, it returns a single value which is the numerical result that's already transferred back
    # to the original signal value
def read_adc_for (select, verbose=True):
    rtrnval = 0
            #DW 2021-09-29-19:51 format is:
            #"<name of selection": [<I2C addr of adc>, <pin of adc>, <unit of measurement>, <optional gain used to convert back to original scale>],
            #for the gain, if the Rdivider had a transfer func of 1/(2+1)=0.333 then the inverse gain will be (0.333)^-1= (1/3)^-1 = 3, so multiplying by 3 
            #puts the voltage level back at the magnitude of what we were sensing
            #TODO need to add the gain terms for the currents
            #TODO need to add the gain terms for temp sense
            #   Name        :  addr pin unit gain_conversion
    choices = {
            "valve1_current": [0x48, 0, 'A', vadc_to_current],
            "valve2_current": [0x48, 1, 'A', vadc_to_current],
            "valve3_current": [0x48, 2, 'A', vadc_to_current],
            "valve4_current": [0x48, 3, 'A', vadc_to_current],
            "valve5_current": [0x49, 0, 'A', vadc_to_current],
            "valve6_current": [0x49, 1, 'A', vadc_to_current],
            "solar_current" : [0x49, 2, 'A', vadc_to_current],
            "ps_current"    : [0x49, 3, 'A', vadc_to_current],
            "vbatt_sense"   : [0x4a, 0, 'V', (49.9+523)/49.9],
            "temp_sense"    : [0x4a, 1, 'deg_C', vadc_to_temp],
            "pot"           : [0x4a, 2, 'V', 1],
            "5v_sense"      : [0x4b, 0, 'V', (49.9+102)/49.9],
            "9v_sense"      : [0x4b, 1, 'V', (49.9+221)/49.9],
            "solar_sense"   : [0x4b, 2, 'V', (49.9+523)/49.9],
            "vin_sense"     : [0x4b, 3, 'V', (49.9+523)/49.9]
            }
    #DW 2021-09-29-20:12 if 'all' is selected, loop through all options and return a dict instead of a single atom value
    if select == 'all':
        rtrnval = {}
        for key in choices.keys():
            choice = choices[key]
            rtrnval[key] = read_adc_for_internal(key, choice, verbose=verbose)
    elif select in choices:
        choice = choices[select]
        rtrnval = read_adc_for_internal(select, choice, verbose=verbose)
    else:
        print(f"Select:'{select}' is not an option in Choices:{list(choices.keys())}")
    return rtrnval


#########################################
#   soil moisture sensor functionality  #
#########################################
def read_soil_sensor():
    try:
        i2c_bus = board.I2C()
        i2c_soil = Seesaw(i2c_bus, addr=0x36)
        soilmoisture = i2c_soil.moisture_read()
        soiltemp = i2c_soil.get_temp()
    except Exception as e:
        print(e)
        soilmoisture = 0
        soiltemp = 0

    # print(f"Soil Moisture: {soilmoisture}, Soil Temp: {soiltemp}")
    return soilmoisture, soiltemp


#####################################
#    BME280 sensor functionality    #
#####################################
def read_baro_sensor():
    # TODO: remove humidity artifacts from baro method
    bus = smbus.SMBus(1)  # BME280 address, 0x76(118)
    # Read data back from 0x88(136), 24 bytes
    b1 = bus.read_i2c_block_data(0x77, 0x88, 24)  # Convert the data

    # Temp coefficients
    dig_T1 = b1[1] * 256 + b1[0]
    dig_T2 = b1[3] * 256 + b1[2]
    if dig_T2 > 32767:
        dig_T2 -= 65536
    dig_T3 = b1[5] * 256 + b1[4]
    if dig_T3 > 32767:
        dig_T3 -= 65536
    # Pressure coefficients
    dig_P1 = b1[7] * 256 + b1[6]
    dig_P2 = b1[9] * 256 + b1[8]
    if dig_P2 > 32767:
        dig_P2 -= 65536
    dig_P3 = b1[11] * 256 + b1[10]
    if dig_P3 > 32767:
        dig_P3 -= 65536
    dig_P4 = b1[13] * 256 + b1[12]
    if dig_P4 > 32767:
        dig_P4 -= 65536
    dig_P5 = b1[15] * 256 + b1[14]
    if dig_P5 > 32767:
        dig_P5 -= 65536
    dig_P6 = b1[17] * 256 + b1[16]
    if dig_P6 > 32767:
        dig_P6 -= 65536
    dig_P7 = b1[19] * 256 + b1[18]
    if dig_P7 > 32767:
        dig_P7 -= 65536
    dig_P8 = b1[21] * 256 + b1[20]
    if dig_P8 > 32767:
        dig_P8 -= 65536
    dig_P9 = b1[23] * 256 + b1[22]
    if dig_P9 > 32767:
        dig_P9 -= 65536  # BME280 address, 0x77
    # Read data back from 0xA1(161), 1 byte
    dig_H1 = bus.read_byte_data(0x77, 0xA1)  # BME280 address, 0x76
    # Read data back from 0xE1(225), 7 bytes
    b1 = bus.read_i2c_block_data(0x77, 0xE1, 7)  # Convert the data

    # Humidity coefficients
    dig_H2 = b1[1] * 256 + b1[0]
    if dig_H2 > 32767:
        dig_H2 -= 65536
    dig_H3 = (b1[2] & 0xFF)
    dig_H4 = (b1[3] * 16) + (b1[4] & 0xF)
    if dig_H4 > 32767:
        dig_H4 -= 65536
    dig_H5 = (b1[4] / 16) + (b1[5] * 16)
    if dig_H5 > 32767:
        dig_H5 -= 65536
    dig_H6 = b1[6]
    if dig_H6 > 127:
        dig_H6 -= 256  # BME280 address, 0x76(118)

    # Select control humidity register, 0xF2(242)
    #		0x01(01)	Humidity Oversampling = 1
    bus.write_byte_data(0x77, 0xF2, 0x01)

    # Select Control measurement register, 0xF4(244)
    #		0x27(39)	Pressure and Temperature Oversampling rate = 1
    #					Normal mode
    bus.write_byte_data(0x77, 0xF4, 0x27)
    # BME280 address, 0x76(118)
    # Select Configuration register, 0xF5(245)
    #		0xA0(00)	Stand_by time = 1000 ms
    bus.write_byte_data(0x77, 0xF5, 0xA0)
    time.sleep(0.5)  # BME280 address, 0x76(118)
    # Read data back from 0xF7(247), 8 bytes
    # Pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB
    # Temperature xLSB, Humidity MSB, Humidity LSB
    data = bus.read_i2c_block_data(0x77, 0xF7, 8)

    # Convert pressure and temperature data to 19-bits
    adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
    adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16  # Convert the humidity data
    adc_h = data[6] * 256 + data[7]

    # Temperature offset calculations
    var1 = (adc_t / 16384.0 - dig_T1 / 1024.0) * dig_T2
    var2 = ((adc_t / 131072.0 - dig_T1 / 8192.0) * (adc_t / 131072.0 - dig_T1 / 8192.0)) * dig_T3
    t_fine = (var1 + var2)
    cTemp = (var1 + var2) / 5120.0
    fTemp = cTemp * 1.8 + 32

    # Pressure offset calculations
    var1 = (t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * dig_P6 / 32768.0
    var2 = var2 + var1 * dig_P5 * 2.0
    var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
    var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * dig_P1
    p = 1048576.0 - adc_p
    p = (p - (var2 / 4096.0)) * 6250.0 / var1
    var1 = dig_P9 * p * p / 2147483648.0
    var2 = p * dig_P8 / 32768.0
    pressure = (p + (var1 + var2 + dig_P7) / 16.0) / 100

    # Humidity offset calculations
    var_H = (t_fine - 76800.0)
    var_H = (adc_h - (dig_H4 * 64.0 + dig_H5 / 16384.0 * var_H)) * (
                dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * var_H * (1.0 + dig_H3 / 67108864.0 * var_H)))
    humidity = var_H * (1.0 - dig_H1 * var_H / 524288.0)
    if humidity > 100.0:
        humidity = 100.0
    elif humidity < 0.0:
        humidity = 0.0

    # packages everything up all nice and neat, returns as list.
    data = [cTemp, fTemp, pressure, humidity]
    return data
