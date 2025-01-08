import pandas as pd

def get_values_from_csv(files, column_name):
    all_values = []
    
    for filename in files:
        # Read the CSV file into a DataFrame, handling the BOM
        df = pd.read_csv(filename, encoding='utf-8-sig')
        
        # Extract the specific values from the specified column
        values = df[column_name].tolist()
        
        # Append to all_values
        all_values.append(values)
    
    return all_values

def calculate_error_values(files, column_name, input_value, max_current):
    values_list = get_values_from_csv(files, column_name)
    all_error_values = []
    
    for values in values_list:
        error_values = [(abs(input_value - value) / max_current) * 100 for value in values]
        all_error_values.append(error_values)
        
    return all_error_values

# Example usage with multiple files:
filenames = ['test.csv', 'test1.csv']  # List of CSV files
column_name = 'channel_1 (nA)'
input_value = 90
max_current = 100

all_errors = calculate_error_values(filenames, column_name, input_value, max_current)
for index, errors in enumerate(all_errors):
    print(f"Errors for {filenames[index]}:")
    print(errors)
