
import time
import requests

bufer = "http://10.11.25.139/io/t1/adc/data_acquisition/buffer_size/value.json"
collect = "http://10.11.25.139/io/t1/probe/calibration/set_temperature_button/value.json"


# requests.put(bufer,'250')
# time.sleep(1)
# requests.put(collect,'true')
# time.sleep(1)
while True:
    for i in range(1, 1001):  # Changed to iterate from 1 to 1000
        requests.put(collect, 'true')
        time.sleep(1)
# time.sleep(5)
# requests.put(url,'"2"')
# time.sleep(5)
