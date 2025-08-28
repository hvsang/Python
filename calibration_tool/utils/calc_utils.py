import numpy as np


def convert_value_keithley(input_current, unit_channel):
    unit_list = {"m": 1e-3, "µ": 1e-6, "n": 1e-9, "p": 1e-12, "k": 1e3}
    for unit in unit_list:
        if unit_channel[0] == unit:
            input_current /= unit_list[unit]
    return input_current


def compute_input(full_scale_range):
    scale_factors = [-0.9, -0.75, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 0.75, 0.9]
    return [full_scale_range * s for s in scale_factors]


def compute_input_charge(full_scale_range):
    scale_factors = [0.1, 0.25, 0.5, 0.75, 0.9]
    return [full_scale_range * 1e-9 * s for s in scale_factors]


def check_relative_error(max_input_range, input_current, data_collect, unit_channel):
    data_handle = {}
    converted_keithley_value = convert_value_keithley(
        input_current, unit_channel)
    data_handle["Input ("+unit_channel + ")"] = converted_keithley_value
    data_handle["Error (%)"] = abs(np.array(data_collect) -
                                   converted_keithley_value) * 100 / max_input_range

    result = []
    for i in data_handle["Error (%)"]:
        if i <= 0.1:
            result.append("Pass")
        elif i > 0.1 and i <= 1:
            result.append("Acceptable")
        else:
            result.append("Fail")

    data_handle["Result"] = result
    return data_handle
