import pandas as pd
from utils.calc_utils import check_relative_error
from utils.device_utils import get_unit, set_source_keithley, get_data_channel


def column_name(channel_number, unit):
    return f"Channel_{channel_number}({unit})"


def result(input_current, channel_number, total_samples, full_scale_range,
           time_delay_keithley, time_delay_get_data, device_scale=1):
    data = []
    for i in input_current:
        print(i * device_scale)
        set_source_keithley(float(i) * device_scale, time_delay_keithley)
        data_collect = get_data_channel(
            channel_number, total_samples, time_delay_get_data)
        dict = {column_name(channel_number, get_unit()): data_collect}
        dict.update(check_relative_error(
            full_scale_range, i, data_collect, get_unit()))

        df = pd.DataFrame(dict)
        data.append(df)
    return data
