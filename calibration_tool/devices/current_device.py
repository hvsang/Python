import time
import requests
from utils.calc_utils import compute_input
from utils.file_utils import format_file
from logic.main_logic import result


def current_device(channel_number="", total_samples=0, range_device=None, device_config=None, ip=""):
    def scale_full_range(r, full_scale):
        scale_map = {**{k: (1e9, "na") for k in (0, 1)},
                     **{k: (1e6, "ua") for k in (2, 3, 4, 5)},
                     **{k: (1e3, "ma") for k in (6, 7)}}
        scale, unit = scale_map.get(r, (1, "A"))
        return full_scale * scale, unit

    if int(channel_number) > device_config["channel_number"]:
        print("Invalid channel")
        return

    range_path = f"http://{ip}{device_config['range_path']}"
    units_path = f"http://{ip}/{device_config['units']}"
    td_keithley, td_get = device_config["time_set_keithley"], device_config["time_get_data"]

    sel = input("Ranges to run (e.g. all, 0,2,5): ").strip().lower()
    auto_sel = input(
        "Auto collect ranges (e.g. 5,6 or none): ").strip().lower()

    run_ranges = range_device if sel in ("", "all") else [
        int(x) for x in sel.split(",") if x.isdigit()]
    auto_ranges = [int(x) for x in auto_sel.split(
        ",") if x.isdigit()] if auto_sel not in ("", "none") else []

    for r in run_ranges:
        auto_collect = r in auto_ranges
        if not auto_collect and input(f"Set up range {r}? Enter 'ok' to continue: ") != "ok":
            print(f"Skipped range {r}")
            continue

        full_scale = device_config["max_current_range"][str(r)]
        input_cur = compute_input(full_scale)
        full_scale, units = scale_full_range(r, full_scale)

        requests.put(units_path, f'"{units}"')
        requests.put(range_path, f'"{r}"')

        print(f"Running -> Range {r}, Channel {channel_number}")
        time.sleep(10)

        data = result(input_cur, channel_number, total_samples,
                      full_scale, td_keithley, td_get, 1, auto_collect)
        format_file(channel_number, data, str(r))
