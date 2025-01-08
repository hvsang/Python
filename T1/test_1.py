# Import libraries
import requests  # Call to html server - library has to be downloaded
import time  # Timestamps
import csv  # csv file handling
# IP address of T1. Change as needed.
ipaddr = "10.11.25.139"
t1_ip = "http://" + ipaddr
# List files for results. T1_data is a list of lists.
t1_data = []
t1_data_entry = []
# Prompt for number of readings and interval between readings
print("Capture a set of B field values from the T1\n")
num = eval(input("How many readings? "))
num = min(num, 300)  # Cap number of readings
interval = eval(input("Time interval? "))
interval = max(interval, 0.00001)  # Restrict smallest interval
# Define range settings
b_ranges = ['28kG', '7kG', '2.8kG', '700G']
# Get range setting and translate
t1_range = requests.get(t1_ip + "/io/t1/range/value.json")
t1_range = t1_range.json()
t1_range = int(t1_range)
t1_range = b_ranges[t1_range]
# Get sample rate setting
rate = {"0": 2800, "1": 700, "2": 2800, "3": 700}
t1_rate = requests.get(t1_ip + "/io/t1/adc/rate/value.json")
t1_rate = t1_rate.json()

t1_units = requests.get(t1_ip + "/io/t1/adc/channel_1/units.json")
t1_units = t1_units.json()
# Print header lines to console
print("T1 range: ", t1_range, ", T1 sample rate: ", t1_rate, " Sa/sec")
print("Collecting ", num, "readings at", interval,
      "second intervals from", ipaddr, "\n")
print(f'Time (sec) Field ({t1_units})')
ctr = 0
# Collect values
while num > 0:
    # ------------------------------------------------------------------
    # Get field data from T1 html server
    ra = requests.get(t1_ip + "/io/t1/adc/channel_1/value.json")
# Convert from text to float
    vala = ra.json()
# Increment time counter
    tctr = (ctr+1)*interval
# Print to console
    print("{:9.6f} {:+12.6f}".format(tctr, vala))
# Add data to table
    t1_data_entry = [1, 2]
    t1_data_entry = [tctr, vala]
    t1_data[len(t1_data):] = [t1_data_entry]
# Step counters and wait to get next reading before looping
    num = num - 1
    ctr = ctr + 1
    time.sleep(interval)
# --------------------------------------------------------------------
# Prompt for csv file save
time.sleep(.5)
print("\n")
response = input("Save csv file (y/n)?")
if (response == 'y'):
    saveName = input("File name? ")
    if (len(saveName) == 0):
        saveName = "t1_data"
    saveName = saveName + ".csv"
    print("Saving to file ", saveName, "in Python directory")
    with open(saveName, 'a', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(["Time (sec)", f'Field ({t1_units})'])
        writer.writerows(t1_data)
        writer.writerow([" "])
    csvFile.close()
    print("File saved - press enter to exit")
