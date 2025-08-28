from utils.file_utils import format_file
from logic.main_logic import result


def voltage_device(channel_number, total_samples, range_select,
                   device_config, get_unit, set_source_keithley, get_data_channel):
    full_scale_range = device_config["max_current_range"][f"{range_select}"]
    input_current = device_config["source_keithley"][f"{range_select}"]
    channel_size = device_config["channel_number"]
    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]

    if int(channel_number) > channel_size:
        print("Over channel size")
    else:
        data = result(input_current, channel_number,
                      total_samples, full_scale_range, time_delay_keithley, time_delay_get_data,
                      get_unit, set_source_keithley, get_data_channel)
        file_result = format_file(channel_number, data)
        return file_result
