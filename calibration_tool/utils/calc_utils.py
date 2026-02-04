import numpy as np


def parse_user_selection(user_selected, range_device, channel_size):
    tasks = []

    if user_selected.lower() == "all":
        tasks = [(r, list(range(1, channel_size + 1))) for r in range_device]
    else:
        parts = user_selected.split()
        for part in parts:
            if part.lower().startswith("ch:"):
                channels = [int(c) for c in part[3:].split(",") if c.isdigit()]
                tasks.extend((r, channels) for r in range_device)
            elif ":" in part:
                r, chs = part.split(":", 1)
                try:
                    r_int = int(r)
                except ValueError:
                    print(f"Range {r} does not exist")
                    return
                channels = [int(c) for c in chs.split(",") if c.isdigit()]
                tasks.append((r_int, channels))
            else:
                try:
                    r_int = int(part)
                    tasks.append((r_int, list(range(1, channel_size + 1))))
                except ValueError:
                    print(f"Range {part} does not exist")
                    return
    return tasks


def convert_value_keithley(input_current, unit_channel):
    unit_list = {"m": 1e-3, "µ": 1e-6, "u": 1e-6,
                 "n": 1e-9, "p": 1e-12, "k": 1e3}
    for unit in unit_list:
        if unit_channel[0] == unit:
            input_current /= unit_list[unit]
    return input_current


def compute_input(full_scale_range):
    scale_factors = [-0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
                     0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05, -0.05, -0.15, -0.25, -0.35, -0.45, -0.55, -0.65, -0.75, -0.85]
    return [full_scale_range * s for s in scale_factors]


def compute_input_charge(full_scale_range):
    scale_factors = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                     0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
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
