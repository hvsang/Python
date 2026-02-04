import sys
sys.dont_write_bytecode = True

from devices.field_device import field_device
from devices.voltage_device import voltage_device
from devices.charge_device import charge_device
from devices.current_device import current_device
from utils.device_utils import get_device_name, get_data_json, is_device_valid, get_path, set_context
from config import ip, path


def main():
    device_name = get_device_name(ip)
    total_samples = 20
    device_information = get_data_json(path)

    if not is_device_valid(device_name, device_information):
        print("The device name incorrect")
        return

    base_devices = ("x3256", "ix512", "ix256-f2", "i128-micro", "i2")
    device_component_name = "base" if device_name in base_devices else ""

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

    elif device_name in base_devices:
        range_device = device_information[device_name]["base"]["range"]

        if device_name in ("x3256", "ix512", "ix256-f2", "i128-micro"):
            print("\n=================== User Selection Syntax Help ===================")
            print("You can combine multiple cases separated by spaces.")
            print("Examples:")
            print("  all               -> Run all ranges on all channels")
            print("  2                 -> Run range 2 on all channels")
            print("  3:12,56           -> Run range 3 only on channels 12 and 56")
            print("  ch:5,6            -> Run all ranges but only on channels 5 and 6")
            print("  2 3:12,56 ch:5,6  -> Combine multiple cases:")
            print("                        Range 2 on all channels")
            print("                        Range 3 on channels 12 and 56")
            print("                        All ranges on channels 5 and 6")
            print("===================================================================\n")
            user_selected_range = input("Enter User Selection: ").strip()
            charge_device(total_samples, "base", range_device,
                          device_information[device_name]["base"], ip, user_selected_range)
        else:
            user_selected_range = input(
                "Enter User Selection Range (0-7), comma-separated, range (e.g. 1-3), or 'all': "
            ).strip().lower()
            channel_number = input("Enter channel number: ")
            charge_device(total_samples, "base", range_device,
                          device_information[device_name]["base"], ip, user_selected_range, channel_number)

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
