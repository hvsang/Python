import time
import threading
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, KeyCode

TOGGLE_KEY = KeyCode(char="b")
clicking = False
mouse = Controller()
click_count = 0  # Counter to track the number of clicks


def clicker():
    global click_count
    while True:
        while clicking and click_count < 100000000000:  # Run loop for 100 clicks
            mouse.click(Button.left, 1)
            click_count += 1  # Increment click count after each click
            print(click_count)
            time.sleep(0.01)
        time.sleep(0.01)  # Wait even when not clicking


def toggle_event(key):
    global clicking, click_count
    if key == TOGGLE_KEY:
        clicking = not clicking
        if not clicking:  # Reset click count when toggling off
            click_count = 0


click_thread = threading.Thread(target=clicker)
click_thread.start()

with Listener(on_press=toggle_event) as listener:
    listener.join()
