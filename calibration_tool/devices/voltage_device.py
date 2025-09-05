from utils.file_utils import format_file
from logic.main_logic import result
from utils.calc_utils import compute_input


def voltage_device(channel_number, total_samples, range_select, device_config):
    full_scale_range = device_config["max_current_range"][f"{range_select}"]
    input_current = compute_input(full_scale_range)
    channel_size = device_config["channel_number"]
    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]

    if int(channel_number) not in channel_size:
        print("Invalid channel")
        return

    data = result(input_current, channel_number, total_samples,
                  full_scale_range, time_delay_keithley, time_delay_get_data)
    format_file(channel_number, data, f"{range_select}")
