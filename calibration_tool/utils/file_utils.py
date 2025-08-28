import os
import shutil
import pandas as pd
import time


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def move_file(excel_path, target_dir, i, range_val):
    base_dir = os.path.join("Result", target_dir)
    sub_dir = f"range_{range_val}" if range_val else ""
    if sub_dir:
        ensure_dir(os.path.join(base_dir, sub_dir))
    else:
        ensure_dir(base_dir)

    filename = f"channel_{i}({range_val}).xlsx"
    destination_path = os.path.join(
        base_dir, sub_dir, filename) if sub_dir else os.path.join(base_dir, filename)

    shutil.move(excel_path, destination_path)


def check_results(excel_path):
    df = pd.read_excel(excel_path, sheet_name=None)
    count_fail, count_accept = 0, 0

    for _, df_sheet in df.items():
        col_strs = df_sheet.astype(str)
        for column in col_strs.columns:
            if col_strs[column].str.contains("Fail").any():
                count_fail += 1
                break
            elif col_strs[column].str.contains("Acceptable").any():
                count_accept += 1
                break
    return count_fail, count_accept


def format_file(i, data, range_val=""):
    result_dir = os.path.join("Result", "Pass")
    sub_dir = f"range_{range_val}" if range_val else ""
    if sub_dir:
        ensure_dir(os.path.join(result_dir, sub_dir))
    else:
        ensure_dir(result_dir)

    excel_path = os.path.join(result_dir, sub_dir, f"channel_{i}({range_val}).xlsx") if sub_dir else os.path.join(
        result_dir, f"channel_{i}({range_val}).xlsx")

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        for idx, df in enumerate(data, start=1):
            df.to_excel(writer, sheet_name=f"Value_{idx}", index_label="Index")
            workbook, worksheet = writer.book, writer.sheets[f"Value_{idx}"]

            formats = {
                "F": workbook.add_format({"bg_color": "red"}),
                "P": workbook.add_format({"bg_color": "green"}),
                "A": workbook.add_format({"bg_color": "yellow"}),
            }
            for prefix, fmt in formats.items():
                worksheet.conditional_format(
                    "E2:E21",
                    {"type": "text", "criteria": "begins with",
                     "value": prefix, "format": fmt},
                )

    time.sleep(0.1)

    count_fail, count_accept = check_results(excel_path)

    if count_fail > 0:
        move_file(excel_path, "Fail", i, range_val)
    elif count_accept > 0:
        move_file(excel_path, "Acceptable", i, range_val)
