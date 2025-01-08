import os
import pandas as pd
import xlsxwriter
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox


class CalibrationTest:
    def __init__(self, root):
        self.root = root
        self.file_paths = []
        self.channels = []
        self.theme = "dark"  # Default theme
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Calibration Test")
        self.root.resizable(False, False)

        self.create_menu()

        self.create_label("Input/Inputs", 0, 0)
        self.input_entry = self.create_entry(0, 1)

        self.create_label("Unit", 1, 0)
        self.unit_entry = self.create_entry(1, 1)

        self.create_label("Full Scale Range	", 2, 0)
        self.full_scale_range_entry = self.create_entry(2, 1)

        self.create_button("Select CSV Files", self.browse_files, 3, 0, tk.W)
        self.create_button("Calculate Errors",
                           self.calculate_errors, 3, 1, tk.W, 31)
        self.export_button = self.create_button(
            "Export CSV Files", self.export_to_excel, 3, 1, tk.E)
        self.export_button.config(state="disabled")

        self.result_text = self.create_text_widget(4, 0, 2)
        self.apply_theme()

    def create_menu(self):
        self.menu_bar = tk.Menu(self.root, tearoff=0)
        self.root.config(menu=self.menu_bar)

        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.theme_menu)
        self.theme_menu.add_command(
            label="Switch to Light Theme", command=self.toggle_theme)

    def create_ui_element(self, element_type, **kwargs):
        grid_kwargs = {k: kwargs.pop(k) for k in [
            'row', 'column', 'padx', 'pady', 'sticky', 'columnspan'] if k in kwargs}
        element = element_type(self.root, **kwargs)
        element.grid(**grid_kwargs)
        return element

    def create_label(self, text, row, column):
        return self.create_ui_element(tk.Label, text=text, font=("Helvetica", 15, "bold"), row=row, column=column, padx=10, pady=10, sticky=tk.W)

    def create_entry(self, row, column):
        return self.create_ui_element(tk.Entry, width=45, font=("Helvetica", 12), row=row, column=column, padx=10, pady=10, sticky=tk.W)

    def create_button(self, text, command, row, column, sticky, padx=10):
        return self.create_ui_element(tk.Button, text=text, command=command, font=("Helvetica", 15, "bold"), row=row, column=column, padx=padx, pady=10, sticky=sticky)

    def create_text_widget(self, row, column, colspan):
        text_widget = self.create_ui_element(tk.Text, width=55, height=15, wrap=tk.WORD, font=(
            "Helvetica", 14), row=row, column=column, columnspan=colspan, padx=10, pady=10)
        text_widget.config(state="disabled")
        for tag, color in zip(['green', 'yellow', 'orange', 'red'], ['green', 'yellow', 'orange', 'red']):
            text_widget.tag_config(tag, background=color, foreground='black')
        return text_widget

    def apply_theme(self):
        if self.theme == "dark":
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            entry_bg = "#3c3f41"
            theme_menu_text = "Switch to Light Theme"
        else:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "#ffffff"
            theme_menu_text = "Switch to Dark Theme"

        button_bg = {"Select CSV Files": "green",
                     "Calculate Errors": "#2196F3", "Export CSV Files": "orange"}

        self.root.configure(bg=bg_color)
        self.root.option_add('*Menu*font', ('Helvetica', 12))

        self.theme_menu.entryconfig(0, label=theme_menu_text)

        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=bg_color, fg=fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=entry_bg, fg=fg_color,
                                 insertbackground=fg_color)
            elif isinstance(widget, tk.Button):
                widget_text = widget.cget("text")
                widget.configure(bg=button_bg.get(
                    widget_text, "#d1d1d1"), fg="black")
            elif isinstance(widget, tk.Text):
                widget.configure(bg=entry_bg, fg=fg_color,
                                 insertbackground=fg_color)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    def browse_files(self):
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        filenames = filedialog.askopenfilenames(
            filetypes=[("CSV files", "*.csv")])

        if filenames:
            self.file_paths = list(filenames)
            self.result_text.insert(
                tk.END, "Selected files:\n" + "\n".join(filenames) + "\n")

        self.result_text.config(state="disabled")
        self.export_button.config(state="disabled")

    def get_values_from_csv(self, files):
        all_values = []
        self.channels = []

        for filename in files:
            try:
                # Read the CSV file into a DataFrame, handling the BOM
                df = pd.read_csv(filename, encoding='utf-8-sig')
                first_row = df.iloc[0].tolist()
                first_row = pd.to_numeric(first_row, errors='coerce')
                series_first_row = pd.Series(first_row)

                channel = series_first_row.abs().idxmax()
                self.channels.append(channel)
                # Check if the column index is within the range of columns
                if 0 <= channel < df.shape[1]:
                    # Extract the specific values from the column at channel
                    values = df.iloc[:, channel].tolist()

                    # Append to all_values
                    all_values.append(values)
                else:
                    messagebox.showerror(
                        "Column index Error", f"Column index '{channel}' is out of range for file '{filename}'")
            except FileNotFoundError:
                messagebox.showerror(
                    "File Error", f"File '{filename}' not found")
            except Exception as e:
                messagebox.showerror(
                    "File Error", f"An error occurred while processing file '{filename}': {e}")

        return all_values

    def calculate_error_values(self, files):
        values_list = self.get_values_from_csv(files)
        input_values = self.input_entry.get().split(',')
        max_current = float(self.full_scale_range_entry.get())
        all_error_values = []

        for index, values in enumerate(values_list):
            input_value = input_values[index] if index < len(
                input_values) else input_values[0]
            error_values = [(abs(float(input_value) - value) /
                             max_current) * 100 for value in values]
            all_error_values.append(error_values)

        return all_error_values

    def calculate_errors(self):
        if not self.file_paths:
            messagebox.showwarning("No Files Selected",
                                   "Please select CSV files first.")
            return

        if not self.validate_inputs():
            return

        all_errors = self.calculate_error_values(self.file_paths)
        self.display_results(all_errors)
        self.export_button.config(state="normal")

    def display_results(self, all_errors):
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Result:\n")

        for index, errors in enumerate(all_errors):
            file_name = os.path.basename(self.file_paths[index])
            result = self.get_result_category(max(errors))
            self.result_text.insert(
                tk.END,
                f"{index + 1}. {file_name}-Channel_{self.channels[index]}: {result}\n",
                self.get_color_tag(result)
            )

        self.result_text.config(state="disabled")

    def export_to_excel(self):
        if not self.validate_export():
            return

        input_values = self.input_entry.get().split(',')
        values_list = self.get_values_from_csv(self.file_paths)
        all_errors = self.calculate_error_values(self.file_paths)

        export_data = self.prepare_export_data(
            input_values, self.channels, values_list, all_errors)
        save_path = self.get_save_path(all_errors)

        if save_path:
            try:
                self.save_to_excel(save_path, export_data, all_errors)
                messagebox.showinfo("Export Complete",
                                    "Data has been exported successfully.")
            except Exception as e:
                messagebox.showerror(
                    "Export Failed", f"An error occurred while saving the file: {e}")

    def validate_export(self):
        if not self.file_paths:
            messagebox.showwarning("No Files Selected",
                                   "Please select CSV files first.")
            return False
        return True

    def prepare_export_data(self, input_values, channels, values_list, all_errors):
        export_data = []
        for index, errors in enumerate(all_errors):
            input_value = float(input_values[index]) if index < len(
                input_values) else float(input_values[0])
            channel = channels[index] if index < len(channels) else channels[0]

            # Blank row for separation
            export_data.append([])
            for idx, (value, error) in enumerate(zip(values_list[index], errors)):
                result = self.get_result_category(error)
                export_data.append(
                    [idx + 1, float(channel), value, float(input_value), error, result])

        return export_data

    def get_result_category(self, error):
        categories = [
            (0.01, "Excellent"),
            (0.1, "Good"),
            (1, "Acceptable"),
            (5, "Poor")
        ]
        for threshold, category in categories:
            if error < threshold:
                return category
        return "OVER"

    def get_color_tag(self, category):
        color_tags = {
            "Excellent": 'green',
            "Good": 'yellow',
            "Acceptable": 'orange',
            "Poor": 'red',
            "OVER": 'white'
        }
        return color_tags[category]

    def get_save_path(self, all_errors):
        max_error = max([max(errors) for errors in all_errors], default=0.0)
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        default_filename = f"{self.get_result_category(float(max_error))}#{current_datetime}.xlsx"

        return filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_filename, filetypes=[("Excel files", "*.xlsx")])

    def save_to_excel(self, save_path, export_data, all_errors):
        with xlsxwriter.Workbook(save_path) as workbook:
            name_sheet = self.get_result_category(
                max(max(errors) for errors in all_errors))
            worksheet = workbook.add_worksheet(name_sheet)
            worksheet.set_tab_color(self.get_color_tag(name_sheet))

            formats = self.create_excel_formats(workbook)
            self.write_headers(worksheet, formats)
            self.write_data_to_excel(worksheet, export_data, formats)

    def create_excel_formats(self, workbook):
        return {
            'center_align': workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1}),
            'bold': workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1}),
            'red_fill': workbook.add_format({'bg_color': 'red', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1}),
            'green_fill': workbook.add_format({'bg_color': 'green', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1}),
            'yellow_fill': workbook.add_format({'bg_color': 'yellow', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1}),
            'orange_fill': workbook.add_format({'bg_color': 'orange', 'bold': True, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': 1})
        }

    def write_headers(self, worksheet, formats):
        worksheet.merge_range(
            'A1:B1', f'Full Scale Range ({self.unit_entry.get()})', formats['bold'])
        worksheet.merge_range(
            'A2:B2', float(self.full_scale_range_entry.get()), formats['bold'])
        worksheet.merge_range('D1:E1', 'Poor', formats['red_fill'])
        worksheet.write('F1', '<5%', formats['bold'])
        worksheet.merge_range('D2:E2', 'Acceptable', formats['orange_fill'])
        worksheet.write('F2', '<1%', formats['bold'])
        worksheet.merge_range('D3:E3', 'Good', formats['yellow_fill'])
        worksheet.write('F3', '<0.1%', formats['bold'])
        worksheet.merge_range('D4:E4', 'Excellent', formats['green_fill'])
        worksheet.write('F4', '<0.01%', formats['bold'])
        worksheet.write('A6', 'STT', formats['bold'])
        worksheet.write('B6', 'Channel', formats['bold'])
        worksheet.write(
            'C6', f'Value ({self.unit_entry.get()})', formats['bold'])
        worksheet.write(
            'D6', f'Input ({self.unit_entry.get()})', formats['bold'])
        worksheet.write('E6', 'Error (%)', formats['bold'])
        worksheet.write('F6', 'Result', formats['bold'])

        worksheet.freeze_panes(6, 0)

    def write_data_to_excel(self, worksheet, export_data, formats):
        row = 5
        for data in export_data:
            for col, value in enumerate(data):
                if col == 5 and value == "Excellent":
                    worksheet.write(row, col, value, formats['green_fill'])
                elif col == 5 and value == "Good":
                    worksheet.write(row, col, value, formats['yellow_fill'])
                elif col == 5 and value == "Acceptable":
                    worksheet.write(row, col, value, formats['orange_fill'])
                elif col == 5 and value == "Poor":
                    worksheet.write(row, col, value, formats['red_fill'])
                else:
                    worksheet.write(row, col, value, formats['center_align'])
            row += 1

    def validate_inputs(self):
        try:
            input_values = self.input_entry.get().split(',')
            unit = self.unit_entry.get()
            max_current = float(self.full_scale_range_entry.get())
        except ValueError:
            messagebox.showerror(
                "Input Error", "Please ensure that all inputs are numeric.")
            return False

        if not input_values or not unit or not max_current:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return False

        return True


# Main program entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = CalibrationTest(root)
    root.mainloop()
