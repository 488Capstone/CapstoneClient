#! /bin/python3
# Above: clientManager.py
# Below: senseSoil.py

# senseManager periodically calls senseBaro and senseSoil every ___ minutes/hours/days,
# or more often if directed.








<<<<<<< HEAD
# Temperature offset calculations
    var1 = ((adc_t) / 16384.0 - (dig_T1) / 1024.0) * (dig_T2)
    var2 = (((adc_t) / 131072.0 - (dig_T1) / 8192.0) * ((adc_t)/131072.0 - (dig_T1)/8192.0)) * (dig_T3)
    t_fine = (var1 + var2)
    cTemp = (var1 + var2) / 5120.0
    fTemp = cTemp * 1.8 + 32

# Pressure offset calculations
    var1 = (t_fine / 2.0) - 64000.0
    var2 = var1 * var1 * (dig_P6) / 32768.0
    var2 = var2 + var1 * (dig_P5) * 2.0
    var2 = (var2 / 4.0) + ((dig_P4) * 65536.0)
    var1 = ((dig_P3) * var1 * var1 / 524288.0 + ( dig_P2) * var1) / 524288.0
    var1 = (1.0 + var1 / 32768.0) * (dig_P1)
    p = 1048576.0 - adc_p
    p = (p - (var2 / 4096.0)) * 6250.0 / var1
    var1 = (dig_P9) * p * p / 2147483648.0
    var2 = p * (dig_P8) / 32768.0
    pressure = (p + (var1 + var2 + (dig_P7)) / 16.0) / 100

# Humidity offset calculations
    var_H = ((t_fine) - 76800.0)
    var_H = (adc_h - (dig_H4 * 64.0 + dig_H5 / 16384.0 * var_H)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * var_H * (1.0 + dig_H3 / 67108864.0 * var_H)))
    humidity = var_H * (1.0 -  dig_H1 * var_H / 524288.0)
    if humidity > 100.0 :
        humidity = 100.0
    elif humidity < 0.0 :
        humidity = 0.0

# Output data to screen
#    print("Temperature in Celsius : %.2f C" %cTemp)
#    print("Temperature in Fahrenheit : %.2f F" %fTemp)
#    print("Pressure : %.2f hPa " %pressure)
#    print("Relative Humidity : %.2f %%" %humidity)

# packages everything up all nice and neat, returns as an array.
    data=[cTemp, fTemp, pressure, humidity]
    return data

baro_data=senseBaro()
print("Temperature in Celsius : %.2f C" %baro_data[0])
print("Temperature in Fahrenheit : %.2f F" %baro_data[1])
print("Pressure : %.2f hPa " %baro_data[2])
print("Relative Humidity : %.2f %%" %baro_data[3])
=======
>>>>>>> 9a98dd0 (Moved good code into capstoneclient.py)
