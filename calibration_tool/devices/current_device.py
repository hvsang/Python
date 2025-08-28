import time
import requests
from utils.calc_utils import compute_input
from utils.file_utils import format_file
from logic.main_logic import result


def current_device(channel_number="", total_samples=0, range_device=[], device_config=None, ip=""):
    def scale_full_range(range_selected, full_scale_range):
        scale_map = {
            **{k: 1e9 for k in (0, 1)},
            **{k: 1e6 for k in (2, 3, 4, 5)},
            **{k: 1e3 for k in (6, 7)},
        }
        return full_scale_range * scale_map.get(range_selected, 1)

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
