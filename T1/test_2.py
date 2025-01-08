# Display big field reading using Tk GUI
# Update reading continuously

import requests		# Call to html server - library has to be downloaded
from tkinter import *

# Set IP address for device here
defipaddr = "10.11.25.139"
print("Set T1 IP address (default is", defipaddr, ") ", end="")
ipaddr = input()
if ipaddr == "":
    ipaddr = defipaddr
print("Using", ipaddr, "\n")

# Choose format
UnitFmt = "{:+11.6f}"

session = requests.Session()


def getIOValue(path):
    return session.get("http://"+ipaddr+"/io"+path+"/value.json", timeout=1.0).json()


def getUnits(path):
    return str(session.get("http://"+ipaddr+"/io"+path+"/units.json", timeout=1.0).json())


def getHostname():
    return str(getIOValue("/net/hostname"))


def getFieldString():
    val = getIOValue("/t1/adc/channel_1")
    return str(UnitFmt.format(val))


def isOverrange():
    return getIOValue("/t1/adc/channel_1/overrange")


# Get T1 ID
t1_Name = getHostname()

# Create Window
B_window = Tk()
B_window_Title = "PTC " + "   " + t1_Name + "   " + ipaddr
B_window.wm_title(B_window_Title)
B_window.minsize(640, 120)
B_window.resizable(False, False)

# Get first field reading
vala = getFieldString()
# B_val=Label(B_window,text=vala,height=1,width=14,justify="right",bd=8,font="Ariel 50 bold",bg="black",fg='green',relief="ridge",padx=32,pady=16)

# Loop to get repeat readings


def draw():
    global B_val
    units = getUnits("/t1/adc/channel_1")
    B_val = Label(B_window, text=vala+" "+units, height=1, width=16, justify="right", bd=8,
                  font='Courier 50 bold', bg="black", fg='green2', relief="ridge", padx=32, pady=16)
    B_val.grid(row=0, column=0)


def updater():
    # Update field value, reject any failed reads
    try:
        vala = getFieldString()
        if isOverrange():
            B_val.configure(text="      Overrange", fg='red2')
        else:
            units = getUnits("/t1/adc/channel_1")
            B_val.configure(text=vala+" "+units, fg='green2')
        B_window.after(100, updater)
    except:
        B_val.configure(text="Comms err", fg='red2')
        B_window.after(1000, updater)


draw()
updater()

B_window.mainloop()
