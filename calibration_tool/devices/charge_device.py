import time
import requests
from utils.calc_utils import compute_input_charge
from utils.file_utils import format_file
from logic.main_logic import result
from utils.device_utils import set_channel_output


def charge_device(total_samples, device_component_name, range_device,
                  device_config, ip, channel_number=None):
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
                    data = result(input_current, channel_number, total_samples,
                                  full_scale_range, time_delay_keithley, time_delay_get_data)
                    format_file(channel, data, f"{range_selected}")
            else:
                if int(channel_number) > channel_size:
                    print("Over channel size")
                else:
                    channel = set_channel_output(channel_number)
                    print(f"Range {range_selected}, Channel {channel_number}:")
                    data = result(input_current, channel_number, total_samples,
                                  full_scale_range, time_delay_keithley, time_delay_get_data)
                    format_file(channel_number, data, f"{range_selected}")
