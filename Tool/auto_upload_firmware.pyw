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
        self.setup_gui()
        self.file_paths = []
        self.stopped = False
        self.gui.resizable(False, False)
        self.port = 80
        self.init_button()

    def setup_gui(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat",
                        font=("Helvetica", 12))
        self.gui.configure(bg="#f0f0f0")

        # Input
        ttk.Label(self.gui, text="IP", font=self.custom_font,
                  background="#f0f0f0").grid(row=0, column=0, sticky="w", pady=5)
        self.ip_entry = ttk.Entry(self.gui, width=30, font=self.custom_font)
        self.ip_entry.grid(row=0, column=1, columnspan=2, sticky="e", pady=5)

        ttk.Label(self.gui, text="Time Interval (seconds)", font=self.custom_font,
                  background="#f0f0f0").grid(row=1, column=0, sticky="w", pady=5)
        self.time_interval_entry = ttk.Entry(
            self.gui, width=30, font=self.custom_font)
        self.time_interval_entry.grid(
            row=1, column=1, columnspan=2, sticky="e", pady=5)

        # Button
        self.choose_file_button = ttk.Button(
            self.gui, text="Choose Firmware", command=self.choose_file, style="TButton")
        self.choose_file_button.grid(row=2, column=0, padx=20, pady=10)

        self.upload_button = ttk.Button(
            self.gui, text="Upload Firmware", command=self.upload_firmware, style="TButton")
        self.upload_button.grid(row=2, column=1, pady=10)

        self.stop_button = ttk.Button(
            self.gui, text="Stop", command=self.stop_upload, state="disabled", style="TButton")
        self.stop_button.grid(row=2, column=2, padx=20, pady=10)

        # Process bar
        self.progress_bar = ttk.Progressbar(
            self.gui, length=455, mode="determinate")
        self.progress_bar.grid(
            row=3, column=0, columnspan=3, sticky="w", pady=10)

        # Text
        self.percent_text = tk.Text(self.gui, height=1, width=5, wrap=tk.WORD,
                                    font=self.custom_font, background="#f0f0f0", borderwidth=0)
        self.percent_text.grid(row=3, column=2, pady=5)
        self.percent_text.insert(tk.END, "0%")
        self.percent_text.config(state="disabled")

        self.time_text = tk.Text(self.gui, height=1, width=6, wrap=tk.WORD,
                                 font=self.custom_font, background="#f0f0f0")
        self.time_text.grid(row=3, column=2, sticky="e", pady=5)
        self.time_text.insert(tk.END, "0s")
        self.time_text.config(state="disabled")

        self.show_screen = tk.Text(
            self.gui, height=10, width=63, wrap=tk.WORD, font=self.custom_font)
        self.show_screen.grid(row=4, column=0, columnspan=3, pady=5)
        self.show_screen.config(state="disabled")

        # Note
        ttk.Label(self.gui, text="Note: Time interval is the time between two uploads. Minimum time is 120 seconds.", font=self.custom_font,
                  background="#f0f0f0").grid(row=5, column=0, sticky="w", columnspan=3, pady=5)

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
                        self.insert_value_with_unit(
                            self.percent_text, percent_complete, "%")
                        self.progress_bar["value"] = percent_complete

            url = f"http://{self.ip_entry.get()}/io/admin/firmware_upload/value.json"
            output, _ = process.communicate()  # Capture stdout
            if output:
                try:
                    # Update the progress bar to its maximum value (100)
                    self.progress_bar["value"] = 100
                    self.insert_value_with_unit(self.percent_text, 100, "%")
                    response_data = json.loads(output)
                    if response_data["status"] == "success":
                        requests.put(url, "true")
                        time.sleep(0.2)
                        requests.put(url, "false")
                        return True
                    else:
                        return False
                except json.JSONDecodeError as e:
                    return False
            else:
                return False

        except subprocess.CalledProcessError as e:
            return False

    def choose_file(self):
        self.clear_log_screen()
        # Update the progress bar to its minimum value (0)
        self.progress_bar["value"] = 0
        self.insert_value_with_unit(self.percent_text, 0, "%")

        self.file_paths = filedialog.askopenfilenames(
            filetypes=[("TAR files", "*.tar.gz")])
        if self.file_paths:
            self.insert_message(
                f"{len(self.file_paths)} Selected files:\n")
            for idx, file_path in enumerate(self.file_paths):
                self.insert_message(f"File {idx + 1}: {file_path}\n")
        else:
            self.insert_message("No files selected!\n", "red")

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

            self.insert_message("Upload count:\n")
            self.enable_stop_button()
            count = 0
            status_upload_fw = True
            while self.connect() and status_upload_fw and not self.stopped:
                for file_path in self.file_paths:
                    if self.stopped:
                        break
                    self.insert_value_with_unit(
                        self.time_text, self.time_interval_entry.get(), "s")
                    self.stop_button.config(state="disabled")
                    file_path_new = self.get_new_file_path(file_path)
                    url = f"http://{self.ip_entry.get()}/root/"
                    status_upload_fw = self.send_file_via_curl(
                        url, file_path_new)
                    count += 1

                    if not status_upload_fw:
                        os.remove(file_path_new)
                        self.insert_message(
                            f"{count}: {os.path.basename(file_path)} upload failed\n", "red")
                        break

                    self.insert_message(
                        f"{count}: {os.path.basename(file_path)} uploaded\n", "green")
                    os.remove(file_path_new)
                    self.stop_button.config(state="normal")
                    self.delay_function(int(self.time_interval_entry.get()))

            self.init_button()
            self.enable_entry()

            if self.stopped:
                self.insert_message("Upload process stopped.\n", "red")
            elif not self.connect():
                self.insert_message(
                    f"{self.ip_entry.get()}:{self.port} is not reachable.\n", "red")

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

    def insert_message(self, message, color="black"):
        self.show_screen.config(state="normal")
        self.show_screen.insert(tk.END, message, color)
        self.show_screen.tag_config(color, foreground=color)
        self.show_screen.tag_add(color, "end - %d chars" %
                                 len(message), tk.END)
        self.show_screen.config(state="disabled")
        self.show_screen.update()

    def insert_value_with_unit(self, widget, value, unit=""):
        # Clear screen
        widget.config(state="normal")
        widget.delete(1.0, "end")
        widget.config(state="disabled")
        # Show screen
        widget.config(state="normal")
        widget.insert("end", f"{value}{unit}")
        widget.config(state="disabled")
        widget.update()

    def init_button(self):
        self.choose_file_button.config(state="normal")
        self.upload_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def delay_function(self, seconds):
        for second in range(seconds):
            if self.stopped:
                break
            self.insert_value_with_unit(self.time_text, int(
                self.time_interval_entry.get()) - (second + 1), "s")
            time.sleep(1)

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

    def check_path_format(self):
        return any("igx" not in file_path for file_path in self.file_paths)

    def check_validate(self):
        check_input = not self.file_paths or not self.ip_entry.get(
        ) or not self.time_interval_entry.get()
        check_validate_input = not self.is_valid_ip(self.ip_entry.get(
        )) or not self.is_valid_integer(self.time_interval_entry.get())

        if check_input or check_validate_input or self.check_path_format():
            if not self.file_paths:
                self.insert_message("Please choose file!\n", "red")
            elif self.check_path_format():
                path_without_igx = [
                    file_path for file_path in self.file_paths if "igx" not in file_path]
                for file_path in path_without_igx:
                    self.insert_message(
                        f"{os.path.basename(file_path)} is not igx format!\n", "red")

            if not self.ip_entry.get():
                self.insert_message("Please enter IP!\n", "red")
            elif not self.is_valid_ip(self.ip_entry.get()):
                self.insert_message(f"IP address is not valid.\n", "red")

            if not self.time_interval_entry.get():
                self.insert_message("Please enter Time Interval!\n", "red")
            elif not self.is_valid_integer(self.time_interval_entry.get()):
                self.insert_message(f"Time Interval is not valid.\n", "red")

            return False

        return True

    def run(self):
        self.gui.mainloop()


if __name__ == "__main__":
    uploader = FirmwareUploader()
    uploader.run()
