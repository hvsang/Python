import os
import psutil


# Function to find all drives
def get_all_drives():
    partitions = psutil.disk_partitions()
    drives = [partition.device for partition in partitions]
    return drives


# Function to search for the file in all drives
def find_file_in_all_drives(target_file):
    drives = get_all_drives()
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            if target_file in files:
                return os.path.join(root, target_file)
    return None


# Example usage
file_to_find = '2024-10-14_8.csv'  # the name of the file you're searching for

file_path = find_file_in_all_drives(file_to_find)
if file_path:
    print(f'File found: {file_path}')
else:
    print('File not found.')
