

def et_calculations():  # TODO: Calculate evapotranspiration
    # I think our system should run on a "day behind" concept
    # i.e. Tuesday's et calculations will be based on the local data from Monday.
    # P = # barometric pressure. Needed in kPa.
    # T_max =
    # T_min =
    # RH_max = # maximum relative humidity as a decimal.
    # RH_min = # minimum relative humidity as a decimal.
    T = (T_max + T_min) / 2  # daily mean air temperature in Celsius
    # R_n = ?
    # G = ?
    # u_2 = ?
    e_omin = 0.6108 ** ((17.27 * T_min) / (T_min + 237.3))
    e_omax = 0.6108 ** ((17.27 * T_max) / (T_max + 237.3))
    e_s = (e_omax + e_omin) / 2  # from a glance, this can be simplified by just taking e_o(T)
    e_a = ((e_omin * RH_max) + e_omax * RH_min) / 2
    delta = (2503 ** ((17.27 * T) / (T + 237.3))) / ((T + 237.3) ** 2)  # from ASCE s.r. - slope of sat. vapor pressure-temp curve
    psycho = 0.000665 * P  # from ASCE standardized reference
    C_n = 900  # constant from ASCE standardized reference
    C_d = 0.34  # constant from ASCE standardized reference

    et_num = 0.408 * delta * (R_n - G) + psycho * (C_n / (T + 273)) * u_2 * (e_s - e_a)
    et_den = psycho + psycho * (1 + C_d * u_2)

    et = et_num / et_den  # millimeters per day
    et = et / 25.4 # inches per day
    return et
