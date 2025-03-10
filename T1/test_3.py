
import time
import requests
from tqdm import tqdm # pip install tqdm

ip = "10.11.25.99"
device_name = "ix256"

# url UTX
url_utx_source = f"http://{ip}/io/{device_name}/calibration/utx_client/source/value.json"
url_utx_output_256_enabled = f"http://{ip}/io/{device_name}/calibration/utx_client/output_256_enabled/value.json"
url_utx_output_256_channel = f"http://{ip}/io/{device_name}/calibration/utx_client/output_256_channel/value.json"

# url IX256
url_ix256_clear_gains_button = f"http://{ip}/io/{device_name}/adc/calibration/clear_gains_button/value.json"
url_ix256_universal_button = f"http://{ip}/io/{device_name}/adc/calibration/all_gains_sequence/universal_button/value.json"

# Setup UT
requests.put(url_utx_source, '"external"')
time.sleep(1)
requests.put(url_utx_output_256_enabled, "true")
time.sleep(1)

# Setup IX256
requests.put(url_ix256_clear_gains_button, "true")
time.sleep(0.5)
requests.put(url_ix256_clear_gains_button, "false")
time.sleep(1)
requests.put(url_ix256_universal_button, "true")
time.sleep(0.5)
requests.put(url_ix256_universal_button, "false")
time.sleep(1)

# Main calibration loop with progress bar
for i in tqdm(range(107, 257), desc=f"Calibrating channels", unit="channel"):
    requests.put(url_utx_output_256_channel, f"{i}")
    time.sleep(0.5)
    url_ix256_universal_button = f"http://{ip}/io/{device_name}/adc/channel_{i}/calibrate_input_sequence/universal_button/value.json"
    requests.put(url_ix256_universal_button, "true")
    time.sleep(0.5)
    requests.put(url_ix256_universal_button, "false")

    # Add progress bar for the 70-second wait
    for _ in tqdm(range(80), desc=f"Waiting for channel {i}", unit="Channel", leave=False):
        time.sleep(1)
    
