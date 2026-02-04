import time
import requests
from utils.calc_utils import compute_input_charge, parse_user_selection
from utils.file_utils import format_file
from logic.main_logic import result
from utils.device_utils import set_channel_output


def charge_device(total_samples, device_component_name, range_device, device_config, ip, user_selected_range, channel_number=None):
    time_delay_keithley = device_config["time_set_keithley"]
    time_delay_get_data = device_config["time_get_data"]

    if device_component_name == "base":
        channel_size = device_config["channel_number"]
        range_selected_path = device_config["range_path"]
        range_path = f"http://{ip}{range_selected_path}"

        if channel_number is None:
            tasks = parse_user_selection(
                user_selected_range, range_device, channel_size)
        else:
            if user_selected_range == "all":
                tasks = [(r, [channel_number]) for r in range_device]
            else:
                try:
                    selected_ranges = []
                    parts = user_selected_range.split(",")
                    for part in parts:
                        part = part.strip()
                        if "-" in part:
                            start, end = map(int, part.split("-"))
                            selected_ranges.extend(range(start, end + 1))
                        else:
                            selected_ranges.append(int(part))
                    # Lọc ra những giá trị nằm trong range_device hợp lệ
                    selected_ranges = [r for r in selected_ranges if r in range_device]

                    if not selected_ranges:
                        print(f"No valid range selected from: {user_selected_range}")
                        return

                    tasks = [(r, [channel_number]) for r in selected_ranges]

                except ValueError:
                    print(f"Invalid range format: {user_selected_range}")
                    return

        for range_selected, channels in tasks:
            if range_selected not in range_device:
                print(f"Range {range_selected} does not exist")
                return

            requests.put(range_path, f'"{range_selected}"')
            time.sleep(2.5)

            max_current_range_path = f'http://{ip}{device_config["max_current_range_path"]}'
            full_scale_range = float(requests.get(max_current_range_path).text)
            input_current = compute_input_charge(full_scale_range)

            for ch in channels:
                if int(ch) > channel_size:
                    print("Invalid channel")
                    return

                channel = set_channel_output(ch)
                print(f"Running -> Range {range_selected}, Channel {channel}")
                data = result(input_current, channel, total_samples,
                              full_scale_range, time_delay_keithley, time_delay_get_data)
                format_file(channel, data, f"{range_selected}")
