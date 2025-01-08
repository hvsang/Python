import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd

# Function to get values from CSV files
def get_values_from_csv(files):
    all_values = []
    
    for index, filename in enumerate(files):
        # Read the CSV file into a DataFrame, handling the BOM
        df = pd.read_csv(filename, encoding='utf-8-sig')
        
        column_name = f"channel_{column_entry.get()[(index * 2)]} (nA)"
        # Extract the specific values from the specified column
        values = df[column_name].tolist()
        
        # Append to all_values
        all_values.append(values)
    
    return all_values

# Function to calculate error values
def calculate_error_values(files, input_value, max_current):
    values_list = get_values_from_csv(files)
    all_error_values = []
    
    for values in values_list:
        error_values = [(abs(input_value - value) / max_current) * 100 for value in values]
        all_error_values.append(error_values)
        
    return all_error_values

# Function to handle file selection
def browse_files():
    filenames = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
    if filenames:
        files_entry.delete(0, tk.END)
        files_entry.insert(tk.END, ", ".join(filenames))

# Function to calculate errors and display them
def calculate_errors():
    filenames = files_entry.get().split(", ")
    if filenames[0]=="":
        return 
    input_value = float(input_entry.get())
    max_current = float(max_current_entry.get())
    
    all_errors = calculate_error_values(filenames, input_value, max_current)
    
    result_text.delete(1.0, tk.END)
    for index, errors in enumerate(all_errors):
        result_text.insert(tk.END, f"Result: {filenames[index]}: ")
        if max(errors) < 0.01:
            result_text.insert(tk.END, f"Excellent\n", 'green')
        elif max(errors) < 0.1:
            result_text.insert(tk.END, f"Good\n", 'yellow')
        elif max(errors) < 1:
            result_text.insert(tk.END, f"Acceptable\n", 'orange')
        elif max(errors) < 5:
            result_text.insert(tk.END, f"Poor\n", 'red')
        else:
            result_text.insert(tk.END, f"OVER\n")

# Function to export values to CSV
def export_to_csv():
    filenames = files_entry.get().split(", ")
    if filenames[0]=="":
        return 
    input_value = float(input_entry.get())
    max_current = float(max_current_entry.get())

    values_list = get_values_from_csv(filenames)
    all_errors = calculate_error_values(filenames, input_value, max_current)
    # Prepare data for export
    export_data = []
    for index, errors in enumerate(all_errors):
        filename = filenames[index]
        # Get the full filename
        full_filename = os.path.basename(filename)
        # Get the filename without extension
        filename_without_extension = os.path.splitext(full_filename)[0]
        result=""
        for value, error in zip(values_list[index], errors):
            if error < 0.01:
                result="Excellent"
            elif error < 0.1:
                result="Good"
            elif error < 1:
                result="Acceptable"
            elif error < 5:
                result="Poor"
            else:
                result="OVER"

            export_data.append([filename_without_extension, column_entry.get()[index * 2], value, input_value, max_current, error, result])
    
    # Create a DataFrame from export_data
    df_export = pd.DataFrame(export_data, columns=['File Name', 'Channel', 'Value', 'Input Value', 'Max Current', 'Error (%)', 'Result'])
    
    # Construct export file name
    export_filename = f"result_{filename.replace('.csv', '')}.csv"
    
    # Ask user to choose where to save the CSV file
    save_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=export_filename, filetypes=[("CSV files", "*.csv")])
    
    if save_path:
        df_export.to_csv(save_path, index=False)
        tk.messagebox.showinfo("Export Complete", "Data has been exported successfully.")
        result_text.insert(tk.END, "\n")

# Create the main application window
root = tk.Tk()
root.title("Error Calculation")

# Create and place widgets
files_label = tk.Label(root, text="Select CSV files:")
files_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

files_entry = tk.Entry(root, width=50)
files_entry.grid(row=0, column=1, padx=10, pady=10)

browse_button = tk.Button(root, text="Browse", command=browse_files)
browse_button.grid(row=0, column=2, padx=10, pady=10)

column_label = tk.Label(root, text="channel:")
column_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

column_entry = tk.Entry(root, width=30)
column_entry.grid(row=1, column=1, padx=10, pady=10)

input_label = tk.Label(root, text="Input:")
input_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)

input_entry = tk.Entry(root, width=10)
input_entry.grid(row=2, column=1, padx=10, pady=10)

max_current_label = tk.Label(root, text="Max Current:")
max_current_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)

max_current_entry = tk.Entry(root, width=10)
max_current_entry.grid(row=3, column=1, padx=10, pady=10)

calculate_button = tk.Button(root, text="Calculate Errors", command=calculate_errors)
calculate_button.grid(row=4, column=1, padx=10, pady=10)

export_button = tk.Button(root, text="Export to CSV", command=export_to_csv)
export_button.grid(row=4, column=2, padx=10, pady=10)

result_label = tk.Label(root, text="Results:")
result_label.grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)

result_text = tk.Text(root, width=60, height=10)
result_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

# Text tag configuration for colors
result_text.tag_config('green', foreground='green')
result_text.tag_config('yellow', foreground='yellow')
result_text.tag_config('orange', foreground='orange')
result_text.tag_config('red', foreground='red')

# Run the main event loop
root.mainloop()
