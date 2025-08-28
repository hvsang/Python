import sys
sys.dont_write_bytecode = True

from config import ip, path
from utils.device_utils import get_device_name, get_data_json, is_device_valid, get_path, set_context
from devices.current_device import current_device
from devices.charge_device import charge_device
from devices.voltage_device import voltage_device
from devices.field_device import field_device


def main():
    device_name = get_device_name(ip)
    total_samples = 20
    device_information = get_data_json(path)

    if not is_device_valid(device_name, device_information):
        print("The device name incorrect")
        return

    device_component_name = ""
    if device_name in ("ix512", "ix256-f2", "i128-micro", "i2"):
        device_component_name = "base"

    # Setup global context for device_utils
    units_path = get_path(device_information, device_name,
                          device_component_name, "units")
    keithley_path = get_path(
        device_information, device_name, device_component_name, "keithley")
    data_path = get_path(device_information, device_name,
                         device_component_name, "data")
    select_channel_path = get_path(
        device_information, device_name, device_component_name, "select_channel")
    set_context(ip, units_path, keithley_path, data_path, select_channel_path)

    if device_name in ("f1", "fx4"):
        range_device = device_information[device_name]["range"]
        if device_name == "f1":
            current_device("1", total_samples, range_device,
                           device_information[device_name], ip)
        elif device_name == "fx4":
            channel_number = input("Enter channel number: ")
            current_device(channel_number, total_samples,
                           range_device, device_information[device_name], ip)

    elif device_name in ("ix512", "ix256-f2", "i128-micro", "i2"):
        range_device = device_information[device_name]["base"]["range"]
        if device_name in ("ix512", "ix256-f2", "i128-micro"):
            charge_device(total_samples, "base", range_device,
                          device_information[device_name]["base"], ip)
        else:
            channel_number = input("Enter channel number: ")
            charge_device(total_samples, "base", range_device,
                          device_information[device_name]["base"], ip, channel_number)

    elif device_name in ("m1", "mx1"):
        range_device = device_information[device_name]["range"]
        range_select = input("Enter range select: ").replace(" ", "").upper()
        if range_select in range_device:
            channel_number = input("Enter channel number: ")
            voltage_device(channel_number, total_samples,
                           range_select, device_information[device_name])
        else:
            print("Invalid select range")

    elif device_name in ("tx2", "t1"):
        range_device = device_information[device_name]["range"]
        range_select = input("Enter range select: ").replace(
            " ", "").replace("u", "µ").lower()
        range_select = range_select[:-1] + range_select[-1].upper()
        if range_select in range_device:
            channel_number = input("Enter channel number: ")
            field_device(channel_number, total_samples,
                         range_select, device_information[device_name])
        else:
            print("Invalid select range")

    else:
        print("Unsupported device")


if __name__ == "__main__":
    main()
