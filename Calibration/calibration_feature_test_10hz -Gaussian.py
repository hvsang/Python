import os
import openpyxl
import numpy as np
import math
import json
import pandas as pd
import time
import requests
import pandas as pd
import shutil
from datetime import datetime
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
    return data.lower()


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
    if device_name == "ix256" and device_component_name == "base" or device_name == "i128-micro":
        for i in data_handle["Error (%)"]:
            if i <= 0.1:
                result.append("Pass")
            elif i > 0.1 and i <= 1:
                result.append("Acceptable")
            else:
                result.append("Fail")
    else:
        for i in data_handle["Error (%)"]:
            if i > 0.1:
                result.append("Fail")
            else:
                result.append("Pass")
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


# Format file


def format_file(i, data, unit="", range=""):
    # Create the result directory if it does not exist
    result_dir = "Pass"
    os.makedirs(result_dir, exist_ok=True)

    # Define the path for the Excel file
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    excel_path = f"{result_dir}/channel_{i}({unit})-{range}#{current_datetime}.xlsx"

    # Create an Excel writer object
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        number = 0
        for df in data:
            number += 1
            df.to_excel(
                writer, sheet_name=f'Value_{number}', index_label="Index")

            # Access the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[f"Value_{number}"]

            # Define formatting styles
            red_format = workbook.add_format({"bg_color": "red"})
            green_format = workbook.add_format({"bg_color": "green"})
            yellow_format = workbook.add_format({"bg_color": "yellow"})

            # Apply conditional formatting
            worksheet.conditional_format(
                "E2:E21", {"type": "text", "criteria": "begins with", "value": "F", "format": red_format})
            worksheet.conditional_format(
                "E2:E21", {"type": "text", "criteria": "begins with", "value": "P", "format": green_format})
            worksheet.conditional_format(
                "E2:E21", {"type": "text", "criteria": "begins with", "value": "A", "format": yellow_format})
    time.sleep(0.1)
    # Define the destination directory and file path
    if device_name == "ix256" and device_component_name == "base" or device_name == "i128-micro":
        fail_dir = "Fail"
        accept_dir = "Acceptable"
        os.makedirs(fail_dir, exist_ok=True)
        os.makedirs(accept_dir, exist_ok=True)
        df = pd.read_excel(excel_path, sheet_name=None)
        count_fail = 0
        count_accept = 0
        for sheetname, df_sheet in df.items():
            for column in df_sheet.columns:
                if df_sheet[column].astype(str).str.contains("Fail").any():
                    count_fail += 1
                    break
                elif df_sheet[column].astype(str).str.contains("Acceptable").any():
                    count_accept += 1
                    break

        if count_fail > 0:
            destination_path = f"{fail_dir}/channel_{i}({unit})-{range}#{current_datetime}.xlsx"
            shutil.move(excel_path, destination_path)
        elif count_accept > 0:
            destination_path = f"{accept_dir}/channel_{i}({unit})-{range}#{current_datetime}.xlsx"
            shutil.move(excel_path, destination_path)
    else:
        fail_dir = "Fail"
        os.makedirs(fail_dir, exist_ok=True)
        df = pd.read_excel(excel_path, sheet_name=None)
        count = 0
        for sheetname, df_sheet in df.items():
            for column in df_sheet.columns:
                if df_sheet[column].astype(str).str.contains("Fail").any():
                    count += 1
                    break
        if count > 0:
            destination_path = f"{fail_dir}/channel_{i}({unit})-{range}#{current_datetime}.xlsx"
            shutil.move(excel_path, destination_path)

# export result


def result(input_current=[], channel_number=0, total_samples=0, full_scale_range=0, time_delay_keithley=0.1, time_delay_get_data=0.1, device_scale=1, gain=1):
    data = []
    for i in input_current:
        print(i*device_scale*gain)
        set_source_keithley(float(i)*device_scale, time_delay_keithley)
        data_collect = get_data_channel(
            channel_number, total_samples, time_delay_get_data)
        dict = {column_name(channel_number): data_collect}
        dict.update(check_relative_error(
            full_scale_range, i*gain, data_collect))

        df = pd.DataFrame(dict)
        data.append(df)
    return data


# calculate calib FX4 device


def fx4_device(channel_number="", total_samples=0):
    channel_size = device_information[f"{device_name}"]["channel_number"]
    if int(channel_number) > channel_size:
        print("Over channel size")
        return
    
    full_scale_range = device_information[f"{device_name}"][
        "max_current_range"][f"{range_select}"]
    input_current = device_information[f"{device_name}"]["source_keithley"][f"{range_select}"]
    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    unit_channel = get_unit()
    
    data = result(input_current, channel_number,
                    total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
    file_result = format_file(channel_number, data, unit_channel, range_select)
    return file_result


# calculate calib I2 device
def i2_device(channel_number="", total_samples=0, frequency=""):
    intergration_device = device_information[f"{device_name}"]["intergration_frequency"]
    channel_size = device_information[f"{device_name}"]["channel_number"]
    if frequency in intergration_device:
        intergration(intergration_frequency)
        full_scale_range = device_information[f"{device_name}"][
            "max_current_range"][f"{range_select}"][f"{frequency}"]
        input_current = device_information[f"{device_name}"]["source_keithley"][f"{range_select}"][f"{frequency}"]
        time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
        time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
        if int(channel_number) > channel_size:
            print("Over channel size")
        else:
            data = result(input_current, channel_number,
                          total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
            file_result = format_file(channel_number, data)
            return file_result
    else:
        print("Frequency value does not exist in file")

# calculate calib IX256 device


def ix256_device(total_samples=0, device_component_name=""):
    full_scale_range = device_information["ix256"][f"{device_component_name}"][
        "max_current_range"][f"{range_select}"]
    input_current = device_information["ix256"][f"{device_component_name}"][
        "source_keithley"][f"{range_select}"]
    time_delay_keithley = device_information["ix256"][
        f"{device_component_name}"]["time_set_keithley"]
    time_delay_get_data = device_information["ix256"][f"{device_component_name}"]["time_get_data"]
    if device_component_name == "base":
        for j in range(1, 257):
            a = set_channel_output(j)
            print("Channel: ", a)
            data = result(input_current, j,
                          total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
            file_result = format_file(j, data)
        return file_result
    else:
        channel_number = 1
        data = result(input_current, channel_number,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
        file_result = format_file(channel_number, data)
        return file_result

# calculate calib I128_micro device


def i128_device(total_samples=0):
    full_scale_range = device_information[f"{device_name}"][
        "max_current_range"][f"{range_select}"]
    input_current = device_information[f"{device_name}"]["source_keithley"][f"{range_select}"]
    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    for j in range(1, 129):
        a = set_channel_output(j)
        print("Channel: ", a)
        data = result(input_current, j,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
        file_result = format_file(j, data)
    return file_result


# calculate calib TX2 device


def tx2_device(channel_number="", total_samples=0):
    channel_size = device_information[f"{device_name}"]["channel_number"]
    if int(channel_number) not in channel_size:
        print("Invalid channel")
        return

    unit_channel = get_unit()
    full_scale_range = device_information[f"{device_name}"]["max_current_range"]
    input_current = device_information[f"{device_name}"]["source_keithley"]
    data = []
    device_scale = 1
    range_10x = ["2.8kG", "700G"]
    probe_channel = ["1", "5"]
    gain = 1
    dict_1 = {"28kG": 2800, "7kG": 700, "2.8kG": 2800, "700G": 700}
    max_current_range = {"28kG": 28000,
                         "7kG": 7000, "2.8kG": 2800, "700G": 700}

    if unit_channel != "V" and (channel_number in probe_channel):
        if range_select in dict_1.keys():
            gain = dict_1[range_select]
        if range_select in max_current_range.keys():
            full_scale_range = max_current_range[range_select]

    if (range_select in range_10x):
        input_current = device_information[f"{device_name}"]["source_keithley_x10"]

    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    data = result(input_current, channel_number,
                  total_samples, full_scale_range, time_delay_keithley, time_delay_get_data, device_scale, gain)

    file_result = format_file(channel_number, data, unit_channel, range_select)
    return file_result


# calculate calib m1 device


def m1_device(channel_number="", total_samples=0):
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

# calculate calib mx1 device


def mx1_device(channel_number="", total_samples=0):
    full_scale_range = device_information[f"{device_name}"]["max_current_range"]
    input_current = device_information[f"{device_name}"]["source_keithley"]
    channel_size = device_information[f"{device_name}"]["channel_number"]
    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    unit_channel = get_unit()
    if int(channel_number) > channel_size:
        print("Over channel size")
        return
    else:
        data = result(input_current, channel_number,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data)
        file_result = format_file(channel_number, data, unit_channel, range_select)
        return file_result

# Calculate calib t1 device


def t1_device(channel_number="", total_samples=0):
    channel_size = device_information[f"{device_name}"]["channel_number"]
    if int(channel_number) not in channel_size:
        print("Invalid channel")
        return

    unit_channel = get_unit()
    full_scale_range = device_information[f"{device_name}"]["max_current_range"]
    input_current = device_information[f"{device_name}"]["source_keithley"]
    data = []
    device_scale = 1
    range_10x = ["2.8kG", "700G"]
    probe_channel = ["1"]
    gain = 1
    dict_1 = {"28kG": 2800, "7kG": 700, "2.8kG": 2800, "700G": 700}
    max_current_range = {"28kG": 28000,
                         "7kG": 7000, "2.8kG": 2800, "700G": 700}

    if unit_channel != "V" and (channel_number in probe_channel):
        if range_select in dict_1.keys():
            gain = dict_1[range_select]
        if range_select in max_current_range.keys():
            full_scale_range = max_current_range[range_select]
        if (range_select in range_10x):
            input_current = device_information[f"{device_name}"]["source_keithley_x10"]

    time_delay_keithley = device_information[f"{device_name}"]["time_set_keithley"]
    time_delay_get_data = device_information[f"{device_name}"]["time_get_data"]
    data = result(input_current, channel_number,
                  total_samples, full_scale_range, time_delay_keithley, time_delay_get_data, device_scale, gain)

    file_result = format_file(channel_number, data, range_select)
    return file_result


# try:
ip = input("Enter ip: ")
device_name = get_device_name()
total_samples = 20
path = "device_information.json"
device_information = get_data_json()
if not is_device_valid():
    print("The device name incorrect")
else:
    if device_name != "m1" and device_name != "mx1":
        range_select = input(
            "Enter range select: ").replace(" ", "").replace("u", "µ").lower()
        range_select = range_select[:-1] + range_select[-1].upper()
        if device_name == "ix256":
            device_component_name = input(
                "Enter device component name of ix256: ")
            units_path = get_units_path(device_component_name)
            keithley_path = get_keithley_path(device_component_name)
            data_path = get_data_path(device_component_name)
            select_channel_path = get_select_channel_path(
                device_component_name)
            device_information = get_data_json()
            if device_component_name not in device_information["ix256"]:
                print("The device component name incorrect")
            else:
                range_device = device_information["ix256"][f"{device_component_name}"]["range"]
                if range_select in range_device:
                    ix256_device(total_samples, device_component_name)
                else:
                    print("Invalid select range")
        else:
            component = ""
            units_path = get_units_path(component)
            keithley_path = get_keithley_path(component)
            data_path = get_data_path(component)
            range_device = device_information[f"{device_name}"]["range"]
            if range_select in range_device:
                if device_name == "i2":
                    intergration_frequency = input(
                        "Enter intergration frequency: ")
                    if not intergration_frequency.isdigit():
                        print("Invalid Intergration frequency")
                    else:
                        frequency = str(intergration_frequency)+"Hz"
                        channel_number = input("Enter channel number: ")
                        if not channel_number.isdigit():
                            print("Invalid channel")
                        else:
                            i2_device(channel_number,
                                      total_samples, frequency)
                elif device_name == "i128-micro":
                    select_channel_path = get_select_channel_path(
                        component)
                    i128_device(total_samples)
                elif device_name == "tx2":
                    channel_number = input("Enter channel number: ")
                    if not channel_number.isdigit():
                        print("Invalid channel")
                    else:
                        tx2_device(channel_number, total_samples)
                elif device_name == "t1":
                    channel_number = input("Enter channel number: ")
                    if not channel_number.isdigit():
                        print("Invalid channel")
                    else:
                        t1_device(channel_number, total_samples)
                else:
                    channel_number = input("Enter channel number: ")
                    if not channel_number.isdigit():
                        print("Invalid channel")
                    else:
                        fx4_device(channel_number, total_samples)
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
                m1_device(channel_number, total_samples)
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
            mx1_device(channel_number, total_samples)

# except:
#     print("Invalid Ip device name")
