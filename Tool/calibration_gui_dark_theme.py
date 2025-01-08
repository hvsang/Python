import os
import csv
import xlsxwriter
import tkinter as tk
from tkinter import filedialog


class CalibrationTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Calibration Test")
        self.file_paths = []  # To store the selected file paths
        self.create_widgets()
        self.root.resizable(False, False)

    def create_widgets(self):
        # Create and place widgets with better layout
        self.root.configure(bg="#2b2b2b")

        column_label = tk.Label(self.root, text="Channel/Channels",
                                bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 15, "bold"))
        column_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.column_channel = tk.Entry(
            self.root, width=45, bg="#3c3f41", fg="#ffffff", font=("Helvetica", 12))
        self.column_channel.grid(
            row=0, column=1, padx=10, pady=10, sticky=tk.W)

        input_label = tk.Label(self.root, text="Input/Inputs",
                               bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 15, "bold"))
        input_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        self.input_entry = tk.Entry(
            self.root, width=45, bg="#3c3f41", fg="#ffffff", font=("Helvetica", 12))
        self.input_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        max_threshold_label = tk.Label(
            self.root, text="Max Threshold", bg="#2b2b2b", fg="#ffffff", font=("Helvetica", 15, "bold"))
        max_threshold_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)

        self.max_threshold_entry = tk.Entry(
            self.root, width=45, bg="#3c3f41", fg="#ffffff", font=("Helvetica", 12))
        self.max_threshold_entry.grid(
            row=2, column=1, padx=10, pady=10, sticky=tk.W)

        select_csv_button = tk.Button(self.root, text="Select CSV Files",
                                      command=self.browse_files, bg="green", fg="black", font=("Helvetica", 15, "bold"))
        select_csv_button.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)

        calculate_button = tk.Button(self.root, text="Calculate Errors", command=self.calculate_errors,
                                     bg="#2196F3", fg="black", font=("Helvetica", 15, "bold"))
        calculate_button.grid(row=3, column=1, padx=29, pady=10, sticky=tk.W)

        self.export_button = tk.Button(self.root, text="Export CSV Files", command=self.export_to_excel,
                                       bg="orange", fg="black", font=("Helvetica", 15, "bold"))
        self.export_button.grid(row=3, column=1, padx=10, pady=10, sticky=tk.E)
        self.export_button.config(state="disabled")

        self.result_text = tk.Text(self.root, width=55, height=15,
                                   wrap=tk.WORD, bg="#3c3f41", fg="#ffffff", font=("Helvetica", 14))
        self.result_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        self.result_text.config(state="disabled")

        # Text tag configuration for colors
        self.result_text.tag_config(
            'green', background='green', foreground='black')
        self.result_text.tag_config(
            'yellow', background='yellow', foreground='black')
        self.result_text.tag_config(
            'orange', background='orange', foreground='black')
        self.result_text.tag_config(
            'red', background='red', foreground='black')

    def browse_files(self):
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)  # Clear result_text
        filenames = filedialog.askopenfilenames(
            filetypes=[("CSV files", "*.csv")])

        if filenames:
            self.file_paths = list(filenames)  # Save the file paths
            self.result_text.insert(
                tk.END, "Selected files:\n" + "\n".join(filenames) + "\n")

        self.result_text.config(state="disabled")
        self.export_button.config(state="disabled")

    def get_values_from_csv(self, files):
        all_values = []
        channels = self.column_channel.get().split(',')

        for index, filename in enumerate(files):
            try:
                channel = channels[index]
            except IndexError:
                channel = channels[0]

            with open(filename, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                column_name = f"channel_{channel} (nA)"
                values = [float(row[column_name])
                          for row in reader if column_name in row]

                if not values:
                    tk.messagebox.showwarning(
                        "Column Error", f"Column '{column_name}' not found in file {filename}.")
                    return []

                all_values.append(values)

        return all_values

    def calculate_error_values(self, files):
        values_list = self.get_values_from_csv(files)
        input_values = self.input_entry.get().split(',')
        max_current = float(self.max_threshold_entry.get())
        all_error_values = []

        for index, values in enumerate(values_list):
            try:
                input_value = input_values[index]
            except IndexError:
                input_value = input_values[0]
            error_values = [(abs(float(input_value) - value) /
                             max_current) * 100 for value in values]
            all_error_values.append(error_values)

        return all_error_values

    def calculate_errors(self):
        if not self.file_paths:
            tk.messagebox.showwarning("No Files Selected",
                                      "Please select CSV files first.")
            return

        if not self.validate_inputs():
            return

        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)  # Clear result_text

        all_errors = self.calculate_error_values(self.file_paths)
        channels = self.column_channel.get().split(',')

        self.result_text.insert(tk.END, "Result:\n")
        for index, errors in enumerate(all_errors):
            file_name = os.path.basename(self.file_paths[index])
            try:
                channel = channels[index]
            except IndexError:
                channel = channels[0]

            self.result_text.insert(
                tk.END, f"{index + 1}. {file_name}-Channel_{channel}: ")
            if max(errors) < 0.01:
                self.result_text.insert(tk.END, f"Excellent\n", 'green')
            elif max(errors) < 0.1:
                self.result_text.insert(tk.END, f"Good\n", 'yellow')
            elif max(errors) < 1:
                self.result_text.insert(tk.END, f"Acceptable\n", 'orange')
            elif max(errors) < 5:
                self.result_text.insert(tk.END, f"Poor\n", 'red')
            else:
                self.result_text.insert(tk.END, f"OVER\n")

        self.result_text.config(state="disabled")
        self.export_button.config(state="normal")

    def export_to_excel(self):
        if not self.file_paths:
            tk.messagebox.showwarning("No Files Selected",
                                      "Please select CSV files first.")
            return

        # Get input values and channels
        input_values = self.input_entry.get().split(',')
        channels = self.column_channel.get().split(',')

        # Fetch values from CSV files and calculate errors
        values_list = self.get_values_from_csv(self.file_paths)
        all_errors = self.calculate_error_values(self.file_paths)

        # Prepare data for export
        export_data = []
        for index, errors in enumerate(all_errors):
            try:
                input_value = input_values[index]
            except IndexError:
                input_value = input_values[0]

            try:
                channel = channels[index]
            except IndexError:
                channel = channels[0]

            export_data.append(
                ['STT', 'Channel', 'Value', 'Input', 'Error (%)', 'Result'])
            for idx, (value, error) in enumerate(zip(values_list[index], errors)):
                if error < 0.01:
                    result = "Excellent"
                elif error < 0.1:
                    result = "Good"
                elif error < 1:
                    result = "Acceptable"
                elif error < 5:
                    result = "Poor"
                else:
                    result = "OVER"
                export_data.append(
                    [idx + 1, float(channel), value, float(input_value), error, result])

            export_data.append([])

        # Construct export file name
        export_filename = "result_.xlsx"

        # Ask user to choose where to save the Excel file
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", initialfile=export_filename, filetypes=[("Excel files", "*.xlsx")]
        )

        if save_path:
            try:
                workbook = xlsxwriter.Workbook(save_path)
                worksheet = workbook.add_worksheet()

                # Define formats
                bold = workbook.add_format(
                    {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
                center_align = workbook.add_format(
                    {'align': 'center', 'valign': 'vcenter', 'border': 1})
                red_fill = workbook.add_format(
                    {'bg_color': 'red', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1})
                green_fill = workbook.add_format(
                    {'bg_color': 'green', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1})
                yellow_fill = workbook.add_format(
                    {'bg_color': 'yellow', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1})
                orange_fill = workbook.add_format(
                    {'bg_color': 'orange', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1})

                # Write the headers with bold and fill formats
                worksheet.merge_range('D1:E1', 'Poor', red_fill)
                worksheet.write('F1', '<5%', center_align)
                worksheet.merge_range('D2:E2', 'Acceptable', orange_fill)
                worksheet.write('F2', '<1%', center_align)
                worksheet.merge_range('D3:E3', 'Good', yellow_fill)
                worksheet.write('F3', '<0.1%', center_align)
                worksheet.merge_range('A3:B3', 'Max Threshold', bold)
                worksheet.merge_range('A4:B4', float(
                    self.max_threshold_entry.get()), center_align)
                worksheet.merge_range('D4:E4', 'Excellent', green_fill)
                worksheet.write('F4', '<0.01%', center_align)

                row = 5
                for data in export_data:
                    for col, value in enumerate(data):
                        # Apply bold format to header row
                        if col == 0 and value == "STT":
                            worksheet.write(row, col, value, bold)
                        elif col == 1 and value == "Channel":
                            worksheet.write(row, col, value, bold)
                        elif col == 2 and value == "Value":
                            worksheet.write(row, col, value, bold)
                        elif col == 3 and value == "Input":
                            worksheet.write(row, col, value, bold)
                        elif col == 4 and value == "Error (%)":
                            worksheet.write(row, col, value, bold)
                        elif col == 5 and value == "Result":
                            worksheet.write(row, col, value, bold)
                        elif col == 5 and value == "Excellent":  # Apply green fill to "Excellent" results
                            worksheet.write(row, col, value, green_fill)
                        elif col == 5 and value == "Good":  # Apply yellow fill to "Good" results
                            worksheet.write(row, col, value, yellow_fill)
                        elif col == 5 and value == "Acceptable":  # Apply orange fill to "Acceptable" results
                            worksheet.write(row, col, value, orange_fill)
                        elif col == 5 and value == "Poor":  # Apply red fill to "Poor" results
                            worksheet.write(row, col, value, red_fill)
                        else:
                            worksheet.write(row, col, value, center_align)
                    row += 1

                workbook.close()

                tk.messagebox.showinfo(
                    "Export Complete", "Data has been exported successfully.")
                self.result_text.insert(tk.END, "\n")
            except Exception as e:
                tk.messagebox.showerror(
                    "Export Failed", f"An error occurred while saving the file: {e}")
        else:
            tk.messagebox.showwarning(
                "Save Cancelled", "No file was selected for saving.")

    def validate_inputs(self):
        try:
            channels = self.column_channel.get().split(',')
            input_values = self.input_entry.get().split(',')
            max_current = float(self.max_threshold_entry.get())
        except ValueError:
            tk.messagebox.showerror(
                "Input Error", "Please ensure that all inputs are numeric.")
            return False

        if not channels or not input_values or not max_current:
            tk.messagebox.showerror(
                "Input Error", "Please fill in all fields.")
            return False

        return True


# Main program entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationTest(root)
    root.mainloop()
