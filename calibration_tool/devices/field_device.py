from utils.file_utils import format_file
from logic.main_logic import result
from utils.calc_utils import compute_input


def field_device(channel_number, total_samples, range_select, device_config):
    full_scale_range = device_config["max_current_range"]
    channel_size = device_config["channel_number"]
    input_current = compute_input(full_scale_range)
    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]
    device_scale = 1
    range_10x = ["2.8kG", "700G"]
    probe_channel = ["1", "5"]

    if int(channel_number) not in channel_size:
        print("Invalid channel")
        return

    if (range_select in range_10x) and (channel_number in probe_channel):
        device_scale = 0.1

    data = result(input_current, channel_number, total_samples, full_scale_range,
                  time_delay_keithley, time_delay_get_data, device_scale)
    format_file(channel_number, data, f"{range_select}")
