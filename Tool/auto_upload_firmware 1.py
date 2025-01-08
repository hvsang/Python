# Note: Tkinter is a library for creating graphical user interfaces (GUIs), and it requires a graphical display to work.

import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import threading
import requests
import socket
import shutil
import time
import json
import os
import re


class FirmwareUploader:
    def __init__(self):
        self.gui = tk.Tk()
        self.gui.title("Upload Firmware")
        self.custom_font = ("Helvetica", 12)
        # Add dark theme colors
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'entry_bg': '#ffffff',
            'button_bg': '#404040',
            'success_button': '#1e8449',
            'primary_button': '#2980b9',
            'danger_button': '#c0392b'
        }
        self.setup_gui()
        self.file_paths = []
        self.stopped = False
        self.gui.resizable(False, False)
        self.port = 80
        self.init_button()

    def setup_gui(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat",
                        font=("Helvetica", 12), background=self.colors['button_bg'])
        self.gui.configure(bg=self.colors['bg'])

        # Update existing widgets with dark theme
        self.create_label("IP Address", 0, 0)
        self.ip_entry = self.create_entry(0, 1)
        self.ip_entry.configure(
            bg=self.colors['entry_bg'], fg=self.colors['fg'], insertbackground=self.colors['fg'])

        self.create_label("Time Interval (seconds)", 1, 0)
        self.time_interval_entry = self.create_entry(1, 1)
        self.time_interval_entry.configure(
            bg=self.colors['entry_bg'], fg=self.colors['fg'], insertbackground=self.colors['fg'])

        # Update buttons with dark theme colors
        self.choose_file_button = self.create_button(
            "Choose Firmware", self.choose_file, 2, 0, tk.W)
        self.choose_file_button.configure(
            bg=self.colors['success_button'], fg=self.colors['fg'])

        self.upload_button = self.create_button("Upload Firmware",
                                                self.upload_firmware, 2, 1, tk.W, 31)
        self.upload_button.configure(
            bg=self.colors['primary_button'], fg=self.colors['fg'])

        self.stop_button = self.create_button(
            "Stop Upload", self.stop_upload, 2, 1, tk.E)
        self.stop_button.configure(
            bg=self.colors['danger_button'], fg=self.colors['fg'])
        self.stop_button.config(state="disabled")

        # Process bar
        self.progress_bar = ttk.Progressbar(
            self.gui, length=540, mode="determinate")
        self.progress_bar.grid(
            row=3, column=0, columnspan=2, sticky="w", pady=10, padx=10)

        self.percent_text = self.create_text_widget(
            3, 1, 1, 5, 1, 12, 80, 5, "e", "0%", 0)

        self.time_text = self.create_text_widget(
            3, 1, 1, 6, 1, 12, 10, 5, "e", "0s")

        # Text
        self.show_screen = self.create_text_widget(4, 0, 2)

        # Note
        self.create_label(
            "Note: Time interval is the time between two uploads. Minimum time is 120 seconds.", 5, 0, 10, 0, 3, 13)

    # Update the percent and time text widgets
    def create_ui_element(self, element_type, **kwargs):
        if element_type == tk.Text:
            kwargs['bg'] = self.colors['entry_bg']
            kwargs['fg'] = self.colors['fg']
        grid_kwargs = {k: kwargs.pop(k) for k in [
            'row', 'column', 'padx', 'pady', 'sticky', 'columnspan'] if k in kwargs}
        element = element_type(self.gui, **kwargs)
        element.grid(**grid_kwargs)
        return element

    def create_label(self, text, row, column, padx=10, pady=10, columnspan=1, size=15):
        return self.create_ui_element(tk.Label, text=text, font=("Helvetica", size, "bold"),
                                      fg=self.colors['fg'], bg=self.colors['bg'],
                                      row=row, column=column, padx=padx, pady=pady, columnspan=columnspan, sticky=tk.W)

    def create_entry(self, row, column):
        return self.create_ui_element(tk.Entry, width=45, font=("Helvetica", 12), row=row, column=column, padx=10, pady=10, sticky=tk.W)

    def create_button(self, text, command, row, column, sticky, padx=10):
        return self.create_ui_element(tk.Button, text=text, command=command, font=("Helvetica", 15, "bold"), row=row, column=column, padx=padx, pady=10, sticky=sticky)

    def create_text_widget(self, row, column, colspan, width=60, height=15, size=14, padx=10, pady=10, sticky="w", text="", borderwidth=1):
        text_widget = self.create_ui_element(tk.Text, width=width, height=height, wrap=tk.WORD,
                                             font=("Helvetica", size), bg=self.colors['bg'],
                                             fg=self.colors['fg'], insertbackground=self.colors['fg'],
                                             row=row, column=column, columnspan=colspan, padx=padx, pady=pady, sticky=sticky, borderwidth=borderwidth)
        text_widget.insert(tk.END, text)
        text_widget.config(state="disabled")
        return text_widget

    def connect(self):
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (self.ip_entry.get(), self.port)
            )
            return True
        except socket.error:
            return False

    def send_file_via_curl(self, url, file_path):
        try:
            cmd = ["curl", "-#", "-X", "PUT", "-T", file_path, url]

            # Start the subprocess and pipe the output
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)
            while True:
                output = process.stderr.readline()
                if process.poll() is not None:
                    break
                if output:
                    if "%" in output:
                        percent = re.search(r'\d+(\.\d+)?', output)
                        percent_complete = float(percent.group())
                        self.insert_percent(percent_complete)
                        self.progress_bar["value"] = percent_complete

            # Update the progress bar to its maximum value (100)
            self.progress_bar["value"] = 100
            self.insert_percent(100)

            state_upload = json.loads(process.stdout.readline())
            url = f"http://{self.ip_entry.get()}/io/admin/firmware_upload/value.json"
            if state_upload["status"] == "success":
                requests.put(url, "true")
                time.sleep(0.2)
                requests.put(url, "false")
                return True
            else:
                return False

        except subprocess.CalledProcessError as e:
            return False

    def choose_file(self):
        self.clear_log_screen()

        self.file_paths = filedialog.askopenfilenames(
            filetypes=[("TAR files", "*.tar.gz")])

        if self.file_paths:
            self.show_screen.config(state="normal")
            self.show_screen.insert(
                "end", f"{len(self.file_paths)} Selected files:\n")
            for idx, file_path in enumerate(self.file_paths):
                self.show_screen.insert(
                    "end", f"File {idx + 1}: {file_path}\n")
        else:
            self.show_screen.config(state="normal")
            self.show_screen.insert("end", "No files selected!\n")

        self.show_screen.config(state="disabled")

    def upload_firmware(self):
        def upload_task():
            self.clear_log_screen()
            self.disable_entry()
            self.choose_file_button.config(state="disabled")
            self.upload_button.config(state="disabled")

            if not self.check_validate():
                self.init_button()
                self.enable_entry()
                return

            if not self.url_exists():
                self.init_button()
                self.enable_entry()
                self.insert_message(
                    f"{self.ip_entry.get()}:{self.port} is not reachable.\n")
                return

            self.insert_message("Upload count:\n")
            self.enable_stop_button()
            count = 0
            status_upload_fw = True
            while self.connect() and status_upload_fw and not self.stopped:
                for file_path in self.file_paths:
                    if self.stopped:
                        break
                    self.insert_time(self.time_interval_entry.get())
                    self.stop_button.config(state="disabled")
                    file_path_new = self.get_new_file_path(file_path)
                    url = f"http://{self.ip_entry.get()}/root/"
                    status_upload_fw = self.send_file_via_curl(
                        url, file_path_new)
                    if not status_upload_fw:
                        os.remove(file_path_new)
                        break

                    count += 1
                    self.insert_message(
                        f"{count}: {os.path.basename(file_path)} uploaded\n")
                    os.remove(file_path_new)
                    self.stop_button.config(state="normal")
                    self.delay_function(int(self.time_interval_entry.get()))

            if self.stopped:
                self.insert_message("Upload process stopped.\n")
                self.init_button()
                self.enable_entry()
            elif not self.connect():
                self.insert_message(
                    f"{self.ip_entry.get()}:{self.port} is not reachable.\n")
                self.init_button()
                self.enable_entry()
            elif not status_upload_fw:
                self.insert_message("Upload firmware failed.\n")
                self.init_button()
                self.enable_entry()

        upload_thread = threading.Thread(target=upload_task)
        upload_thread.start()

    def stop_upload(self):
        self.stopped = True
        self.stop_button.config(state="disabled")

    def enable_stop_button(self):
        self.stopped = False
        self.stop_button.config(state="normal")

    def disable_entry(self):
        self.time_interval_entry.config(state="disabled")
        self.ip_entry.config(state="disabled")

    def enable_entry(self):
        self.time_interval_entry.config(state="normal")
        self.ip_entry.config(state="normal")

    def clear_log_screen(self):
        self.show_screen.config(state="normal")
        self.show_screen.delete(1.0, "end")
        self.show_screen.config(state="disabled")

    def insert_message(self, message):
        self.show_screen.config(state="normal")
        self.show_screen.insert("end", message)
        self.show_screen.config(state="disabled")
        self.show_screen.update()

    def insert_percent(self, percent):
        # Clear screen
        self.percent_text.config(state="normal")
        self.percent_text.delete(1.0, "end")
        self.percent_text.config(state="disabled")
        # Show screen
        self.percent_text.config(state="normal")
        self.percent_text.insert("end", f"{percent}%")
        self.percent_text.config(state="disabled")
        self.percent_text.update()

    def insert_time(self, time):
        # Clear screen
        self.time_text.config(state="normal")
        self.time_text.delete(1.0, "end")
        self.time_text.config(state="disabled")
        # Show screen
        self.time_text.config(state="normal")
        self.time_text.insert("end", f"{time}s")
        self.time_text.config(state="disabled")
        self.time_text.update()

    def init_button(self):
        self.choose_file_button.config(state="normal")
        self.upload_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def delay_function(self, seconds):
        for second in range(seconds):
            if self.stopped:
                break
            self.insert_time(int(self.time_interval_entry.get())-(second+1))
            time.sleep(1)

    def url_exists(self):
        url = f"http://{self.ip_entry.get()}/io/admin/firmware_upload/state/value.json"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP request errors

            try:
                data = response.json()
                return data == "ready"
            except json.JSONDecodeError as e:
                return False
        except requests.exceptions.RequestException as e:
            return False

    def get_new_file_path(self, file_path):
        if os.path.basename(file_path) == "igx.tar.gz":
            return file_path
        else:
            directory = os.path.dirname(file_path)
            file_path_new = f"{directory}/igx.tar.gz"
            shutil.copy(file_path, file_path_new)
            return file_path_new

    def is_valid_ip(self, ip):
        # Define a regular expression pattern for the IP address format
        ip_pattern = r'^\d{1,3}(\.\d{1,3}){3}$'

        # Use the re.match function to check if the input matches the pattern
        if re.match(ip_pattern, ip):
            # Split the IP address into its components and check if each component is in the valid range
            octets = ip.split('.')
            for octet in octets:
                if 0 <= int(octet) <= 255:
                    continue
                else:
                    return False
            return True
        else:
            return False

    def is_valid_integer(self, value):
        try:
            number = int(value)
            return number >= 120
        except ValueError:
            return False

    def check_validate(self):
        check_input = not self.file_paths or not self.ip_entry.get(
        ) or not self.time_interval_entry.get()
        check_validate_input = not self.is_valid_ip(self.ip_entry.get(
        )) or not self.is_valid_integer(self.time_interval_entry.get())

        if check_input or check_validate_input:
            if not self.file_paths:
                self.insert_message("Please choose file!\n")

            if not self.ip_entry.get():
                self.insert_message("Please enter IP!\n")
            elif not self.is_valid_ip(self.ip_entry.get()):
                self.insert_message(f"IP address is not valid.\n")

            if not self.time_interval_entry.get():
                self.insert_message("Please enter Time Interval!\n")
            elif not self.is_valid_integer(self.time_interval_entry.get()):
                self.insert_message(f"Time Interval is not valid.\n")

            return False

        return True

    def run(self):
        self.gui.mainloop()


if __name__ == "__main__":
    uploader = FirmwareUploader()
    uploader.run()
