import os
import sys
import json
import time
import requests
from .http_utils import http_get

# --- Global context ---
ip = None
units_path = None
keithley_path = None
data_path = None
select_channel_path = None


def set_context(ip_addr, u_path, k_path, d_path, ut_path):
    """Set global context for device"""
    global ip, units_path, keithley_path, data_path, select_channel_path
    ip = ip_addr
    units_path = u_path
    keithley_path = k_path
    data_path = d_path
    select_channel_path = ut_path


def get_unit():
    url = f"http://{ip}/{units_path}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip('"')


def set_source_keithley(input_current=0.0, time_delay=0.1):
    url = f"http://{ip}/{keithley_path}"
    response = requests.put(url, str(input_current))
    time.sleep(time_delay)
    data = 1.0
    while response.status_code == 200 and data != input_current:
        data = float(requests.get(url).text)
        return data


def set_channel_output(channel_number=0, time_delay=0.1):
    url = f"http://{ip}/{select_channel_path}"
    response = requests.put(url, str(channel_number))
    time.sleep(time_delay)
    data = 0
    while response.status_code == 200 and data != channel_number:
        data = int(requests.get(url).text)
        return data


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


def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):  # Run exe
        base_path = sys._MEIPASS
    else:  # Run script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)


def get_data_json(path):
    try:
        json_path = get_resource_path(path)
        with open(json_path, "r", encoding="utf-8") as f:
            device_info = json.load(f)
        return device_info
    except:
        return None


def get_device_name(ip):
    url = f"http://{ip}/io/admin/device_type/value.json"
    data = http_get(url)
    return data.strip().lower() if data else None


def is_device_valid(device_name, device_information):
    try:
        return device_name in device_information
    except:
        return False


def get_path(data, device_name, component, key):
    try:
        if component == "":
            return data[device_name][key]
        else:
            return data[device_name][component][key]
    except:
        return None
