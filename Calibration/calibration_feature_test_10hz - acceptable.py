import os
import json
import time
import shutil
import requests
import numpy as np
import pandas as pd
# install all library python to run code (pip install requests/pandas/numpy/openpyxl/xlsxwriter)


# get data_json_file
def get_data_json():
    try:
        with open(path, "r", encoding="utf-8") as jsonfile:
            data_json = json.load(jsonfile)
        return data_json
    except:
        return None


# get_device_name
def get_device_name():
    url = f"http://{ip}/io/admin/device_type/value.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text.replace('"', '')
    return data.strip().lower()


# device_valid
def is_device_valid():
    try:
        return get_device_name() in get_data_json()
    except:
        return False


# get select_channel path
def get_select_channel_path(component=""):
    data = get_data_json()
    try:
        if component == "":
            return data[device_name]["select_channel"]
        else:
            return data[device_name][component]["select_channel"]
    except:
        return None


# set_select_channel_number
def set_channel_output(channel_number=0):
    url = f"http://{ip}/{select_channel_path}"
    response = requests.put(url, str(channel_number))
    data = 0
    while response.status_code == 200 and data != channel_number:
        data = int(requests.get(url).text)
    return data


# get_units_path
def get_units_path(component=""):
    data = get_data_json()
    try:
        if component == "":
            return (data[device_name]["units"])
        else:
            return data[device_name][component]["units"]
    except:
        return None


# get Unit
def get_unit():
    url = f"http://{ip}/{units_path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip('"')


# get_Keithley_path
def get_keithley_path(component=""):
    data = get_data_json()
    try:
        if component == "":
            return data[device_name]["keithley"]
        else:
            return data[device_name][component]["keithley"]
    except:
        return None


# set_source_keithley
def set_source_keithley(input_current=0.0, time_delay=0.1):
    url = f"http://{ip}/{keithley_path}"
    response = requests.put(url, str(input_current))
    time.sleep(time_delay)
    data = 1.0
    while response.status_code == 200 and data != input_current:
        data = float(requests.get(url).text)
        return (data)


# change input current
def convert_value_keithley(input_current):
    unit_channel = get_unit()
    unit_list = {"m": 1e-3, "µ": 1e-6, "n": 1e-9, "p": 1e-12, "k": 1e3}
    for unit in unit_list:
        if unit_channel[0] == unit:
            input_current /= unit_list[unit]
    return input_current


# get_data_path
def get_data_path(component=""):
    data = get_data_json()
    try:
        if component == "":
            return data[device_name]["data"]
        else:
            return data[device_name][component]["data"]
    except:
        return None


# get value 1 channel
def get_data_channel(channel_number, total_samples=1, time_delay_get_data=0.1):
    url = f"http://{ip}/{data_path}/channel_{channel_number}/value.json"
    Data = []
    count = 0
    time.sleep(time_delay_get_data)
    while count < total_samples:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.text
            Data.append(float(data))
        else:
            return None
        time.sleep(0.1)
        count += 1
    return Data


# get column name
def column_name(channel_number):
    col_name = f"Channel_{channel_number}" + \
        "(" + get_unit() + ")"
    return col_name


# calculate Calibration
def check_relative_error(max_input_range, input_current, data_collect):
    data_handle = {}
    converted_keithley_value = convert_value_keithley(input_current)
    data_handle["Input ("+get_unit() + ")"] = converted_keithley_value
    data_handle["Error (%)"] = abs(np.array(data_collect) -
                                   converted_keithley_value)*100/max_input_range

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


# set ingtergration frequency
def intergration(frequency=0):
    url = f"http://{ip}/io/{device_name}/adc/integration_frequency/value.json"
    response = requests.put(url, str(frequency))
    data = 0
    while response.status_code == 200 and data != frequency:
        data = int(requests.get(url).text)
        return data


# Check Excel file and return counts for Fail/Acceptable.
def check_results(excel_path):
    df = pd.read_excel(excel_path, sheet_name=None)
    count_fail, count_accept = 0, 0

    for _, df_sheet in df.items():
        col_strs = df_sheet.astype(str)
        for column in col_strs.columns:
            if col_strs[column].str.contains("Fail").any():
                count_fail += 1
                break
            elif col_strs[column].str.contains("Acceptable").any():
                count_accept += 1
                break
    return count_fail, count_accept


# Create directory if not exists.
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


# Move Excel file to the correct directory.
def move_file(excel_path, target_dir, i, range_val):
    sub_dir = f"range_{range_val}" if range_val else ""
    if sub_dir:
        ensure_dir(os.path.join(target_dir, sub_dir))
    else:
        ensure_dir(target_dir)

    filename = f"channel_{i}({range_val}).xlsx"
    destination_path = os.path.join(
        target_dir, sub_dir, filename) if sub_dir else os.path.join(target_dir, filename)

    shutil.move(excel_path, destination_path)


# Always create Pass directory (with optional range subdir)
def format_file(i, data, range_val=""):
    result_dir = "Pass"
    sub_dir = f"range_{range_val}" if range_val else ""
    if sub_dir:
        ensure_dir(os.path.join(result_dir, sub_dir))
    else:
        ensure_dir(result_dir)

    excel_path = os.path.join(result_dir, sub_dir, f"channel_{i}({range_val}).xlsx") if sub_dir else os.path.join(
        result_dir, f"channel_{i}({range_val}).xlsx")

    # Write data to Excel
    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        for idx, df in enumerate(data, start=1):
            df.to_excel(writer, sheet_name=f"Value_{idx}", index_label="Index")
            workbook, worksheet = writer.book, writer.sheets[f"Value_{idx}"]

            # Apply formatting
            formats = {
                "F": workbook.add_format({"bg_color": "red"}),
                "P": workbook.add_format({"bg_color": "green"}),
                "A": workbook.add_format({"bg_color": "yellow"}),
            }
            for prefix, fmt in formats.items():
                worksheet.conditional_format(
                    "E2:E21",
                    {"type": "text", "criteria": "begins with",
                        "value": prefix, "format": fmt},
                )

    time.sleep(0.1)

    # Decide where to move file
    fail_dir, accept_dir = "Fail", "Acceptable"
    count_fail, count_accept = check_results(excel_path)

    if count_fail > 0:
        move_file(excel_path, fail_dir, i, range_val)
    elif count_accept > 0:
        move_file(excel_path, accept_dir, i, range_val)


# export result
def result(input_current=[], channel_number=0, total_samples=0, full_scale_range=0, time_delay_keithley=0.1, time_delay_get_data=0.1, device_scale=1):
    data = []
    for i in input_current:
        print(i*device_scale)
        set_source_keithley(float(i)*device_scale, time_delay_keithley)
        data_collect = get_data_channel(
            channel_number, total_samples, time_delay_get_data)
        dict = {column_name(channel_number): data_collect}
        dict.update(check_relative_error(full_scale_range, i, data_collect))

        df = pd.DataFrame(dict)
        data.append(df)
    return data


def compute_input(full_scale_range):
    """Compute input currents for calibration (-90% → +90%)."""
    scale_factors = [-0.9, -0.75, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 0.75, 0.9]
    return [full_scale_range * s for s in scale_factors]


# calculate calib FX4, F1 device
def current_device(channel_number="", total_samples=0, range_device=[]):
    def scale_full_range(range_selected, full_scale_range):
        """Scale full scale range depending on unit (nA, µA, mA)."""
        scale_map = {
            **{k: 1e9 for k in (0, 1)},        # A → nA
            **{k: 1e6 for k in (2, 3, 4, 5)},  # A → µA
            **{k: 1e3 for k in (6, 7)},        # A → mA
        }
        return full_scale_range * scale_map.get(range_selected, 1)

    device_config = device_information[f"{device_name}"]

    channel_size = device_config["channel_number"]
    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]

    range_selected_path = device_config["range_path"]
    range_path = f"http://{ip}{range_selected_path}"

    for range_selected in range_device:
        requests.put(range_path, f'"{range_selected}"')
        time.sleep(2.5)

        full_scale_range = device_config["max_current_range"][f"{range_selected}"]
        input_current = compute_input(full_scale_range)

        full_scale_range = scale_full_range(range_selected, full_scale_range)

        if int(channel_number) > channel_size:
            print("Over channel size")
        else:
            print(f"Range {range_selected}, Channel {channel_number}:")
            data = result(input_current, channel_number,
                          total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
            format_file(channel_number, data, f"{range_selected}")


# calculate calib I128_micro, IX256 device
def charge_device(total_samples=0, device_component_name="base", range_device=[], channel_number=None):
    def compute_input_charge(full_scale_range):
        """Compute input currents for charge calibration (10% → 90%)."""
        scale_factors = [0.1, 0.25, 0.5, 0.75, 0.9]
        return [full_scale_range * 1e-9 * s for s in scale_factors]

    device_config = device_information[f"{device_name}"][f"{device_component_name}"]

    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]

    if device_component_name == "base":
        channel_size = device_config["channel_number"]
        range_selected_path = device_config["range_path"]
        range_path = f"http://{ip}{range_selected_path}"
        for range_selected in range_device:
            requests.put(range_path, f'"{range_selected}"')
            time.sleep(2.5)
            max_current_range_path = f'http://{ip}{device_config["max_current_range_path"]}'
            full_scale_range = float(requests.get(max_current_range_path).text)
            input_current = compute_input_charge(full_scale_range)

            if channel_number is None:
                for ch in range(1, channel_size + 1):
                    channel = set_channel_output(ch)
                    print(f"Range {range_selected}, Channel {channel}:")
                    data = result(input_current, ch,
                                  total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
                    format_file(ch, data, f"{range_selected}")
            else:
                if int(channel_number) > channel_size:
                    print("Over channel size")
                else:
                    print(f"Range {range_selected}, Channel {channel_number}:")
                    data = result(input_current, channel_number,
                                  total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
                    format_file(channel_number, data, f"{range_selected}")
    else:
        full_scale_range = device_config["max_current_range"][f"{range_select}"]
        input_current = device_config["source_keithley"][f"{range_select}"]
        channel_size = 2
        data = result(input_current, channel_size,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
        format_file(channel_size, data)


# calculate calib m1, mx1 device
def voltage_device(channel_number="", total_samples=0, range_select="10V"):
    full_scale_range = device_information[f"{device_name}"][
        "max_current_range"][f"{range_select}"]
    input_current = device_information[f"{device_name}"]["source_keithley"][f"{range_select}"]
    channel_size = device_information[f"{device_name}"]["channel_number"]
    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    if int(channel_number) > channel_size:
        print("Over channel size")
    else:
        data = result(input_current, channel_number,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
        file_result = format_file(channel_number, data)
        return file_result


# calculate calib TX2, T1 device
def field_device(channel_number="", total_samples=0):
    full_scale_range = device_information[f"{device_name}"]["max_current_range"]
    channel_size = device_information[f"{device_name}"]["channel_number"]
    data = []
    device_scale = 1
    range_10x = ["2.8kG", "700G"]
    probe_channel = ["1", "5"]
    if int(channel_number) not in channel_size:
        print("Invalid channel")
        return
    if (range_select in range_10x) and (channel_number in probe_channel):
        device_scale = 0.1
    input_current = device_information[f"{device_name}"]["source_keithley"]
    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    data = result(input_current, channel_number,
                  total_samples, full_scale_range, time_delay_keithley, time_delay_get_data, device_scale)

    file_result = format_file(channel_number, data)
    return file_result


try:
    ip = "10.11.25.168"
    device_name = get_device_name()
    total_samples = 20
    path = "device_information.json"
    device_information = get_data_json()
    if not is_device_valid():
        print("The device name incorrect")
    else:
        if device_name != "m1" and device_name != "mx1":
            if device_name == "ix256-f2":
                device_component_name = input(
                    "Enter device component name of ix256: ")
                units_path = get_units_path(device_component_name)
                keithley_path = get_keithley_path(device_component_name)
                data_path = get_data_path(device_component_name)
                select_channel_path = get_select_channel_path(
                    device_component_name)
                device_information = get_data_json()
                if device_component_name not in device_information["ix256-f2"]:
                    print("The device component name is incorrect")
                else:
                    range_device = device_information["ix256-f2"][f"{device_component_name}"]["range"]
                    if not device_component_name == "base":
                        range_select = input("Enter range select: ").replace(
                            " ", "").replace("u", "µ").lower()
                        range_select = range_select[:-
                                                    1] + range_select[-1].upper()
                        if range_select in range_device:
                            charge_device(
                                total_samples, device_component_name, range_device)
                        else:
                            print("Invalid select range")
                    else:
                        charge_device(
                            total_samples, device_component_name, range_device)
            elif device_name in ("ix512", "i128-micro", "i2"):
                units_path = get_units_path("base")
                keithley_path = get_keithley_path("base")
                data_path = get_data_path("base")
                select_channel_path = get_select_channel_path("base")
                device_information = get_data_json()
                range_device = device_information[device_name]["base"]["range"]
                if device_name in ("ix512", "i128-micro"):
                    charge_device(total_samples, "base", range_device)
                else:
                    channel_number = input("Enter channel number: ")
                    if not channel_number.isdigit():
                        print("Invalid channel")
                    else:
                        charge_device(total_samples, "base",
                                      range_device, channel_number)
            elif device_name in ("f1", "fx4"):
                component = ""
                units_path = get_units_path(component)
                keithley_path = get_keithley_path(component)
                data_path = get_data_path(component)
                range_device = device_information[f"{device_name}"]["range"]
                if device_name == "f1":
                    current_device("1", total_samples, range_device)
                elif device_name == "fx4":
                    channel_number = input("Enter channel number: ")
                    if not channel_number.isdigit():
                        print("Invalid channel")
                    else:
                        current_device(
                            channel_number, total_samples, range_device)
            else:
                range_select = input(
                    "Enter range select: ").replace(" ", "").replace("u", "µ").lower()
                range_select = range_select[:-1] + range_select[-1].upper()
                component = ""
                units_path = get_units_path(component)
                keithley_path = get_keithley_path(component)
                data_path = get_data_path(component)
                range_device = device_information[f"{device_name}"]["range"]
                if range_select in range_device:
                    if device_name == "tx2":
                        channel_number = input("Enter channel number: ")
                        if not channel_number.isdigit():
                            print("Invalid channel")
                        else:
                            field_device(channel_number, total_samples)
                    elif device_name == "t1":
                        channel_number = input("Enter channel number: ")
                        if not channel_number.isdigit():
                            print("Invalid channel")
                        else:
                            field_device(channel_number, total_samples)
                else:
                    print("Invalid select range")
        elif device_name == "m1":
            component = ""
            units_path = get_units_path(component)
            keithley_path = get_keithley_path(component)
            data_path = get_data_path(component)
            range_device = device_information[f"{device_name}"]["range"]
            range_select = input(
                "Enter range select: ").replace(" ", "").upper()
            if range_select in range_device:
                channel_number = input("Enter channel number: ")
                if not channel_number.isdigit():
                    print("Invalid channel")
                else:
                    voltage_device(channel_number, total_samples, range_select)
            else:
                print("Invalid select range")
        else:
            component = ""
            units_path = get_units_path(component)
            keithley_path = get_keithley_path(component)
            data_path = get_data_path(component)
            channel_number = input("Enter channel number: ")
            if not channel_number.isdigit():
                print("Invalid channel")
            else:
                voltage_device(channel_number, total_samples)

except:
    print("Invalid Ip device name")
