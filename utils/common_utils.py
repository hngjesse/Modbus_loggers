import os
import shutil
import sys
import csv
from datetime import datetime, timedelta
from typing import TextIO


class Tee:
    """Duplicate terminal output to both stdout and a log file."""
    def __init__(self, *files: TextIO):
        self.files = files

    def write(self, obj: str) -> None:
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self) -> None:
        for f in self.files:
            f.flush()



def get_csv_path(base_folder: str, file_suffix: str, header: list) -> str:
    """
    Create and return the CSV path for the current month, under year-based folders.

    Args:
        base_folder (str): Base directory where the 'data' folder will be created.
        file_suffix (str): Short identifier for the file (e.g., "temp_log", "dc_meter").
        header (list): List of column headers for the CSV file.

    Returns:
        str: Full path to the CSV file.
    """
    now = datetime.now()
    year_folder = os.path.join(base_folder, "data", now.strftime("%Y"))
    month_name = now.strftime("%Y-%m")  # e.g. 2025-10
    os.makedirs(year_folder, exist_ok=True)
    csv_path = os.path.join(year_folder, f"{month_name}_{file_suffix}.csv")

    # Create the CSV file with header if it doesn't exist or is empty
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        with open(csv_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    return csv_path


def cleanup_old_logs(log_folder: str, log_retention_days: int) -> None:
    """
    Delete .log files in `log_folder` older than `log_retention_days`.

    Args:
        log_folder (str): Path to the folder containing log files.
        log_retention_days (int): Number of days to retain log files.
    """
    if not os.path.isdir(log_folder):
        print(f"⚠️ Log folder '{log_folder}' not found.")
        return

    cutoff = datetime.now() - timedelta(days=log_retention_days)
    deleted_count = 0

    for fname in os.listdir(log_folder):
        if not fname.endswith(".log"):
            continue

        fpath = os.path.join(log_folder, fname)
        try:
            # Expect file format: YYYY-MM-DD.log
            fdate = datetime.strptime(fname[:-4], "%Y-%m-%d")

            if fdate < cutoff:
                os.remove(fpath)
                print(f"🗑️ Deleted old log: {fname}")
                deleted_count += 1
        except ValueError:
            # Skip files not following the date pattern
            continue

    if deleted_count == 0:
        print("No old log files found to delete.")
    else:
        print(f"Deleted {deleted_count} old log file(s).")


def get_log_path(log_folder: str) -> str:
    """Return today's log file path, ensuring folder exists."""
    os.makedirs(log_folder, exist_ok=True)
    return os.path.join(log_folder, f"{datetime.now().strftime('%Y-%m-%d')}.log")




def log_rotation(log_folder, log_file, current_log_date, log_retention_days) -> tuple:
    """
    Checks if a new day has started, and if so, rotates the log file.

    Returns:
        new_log_file (file object)
        new_log_date (datetime.date)

    Returns:
        tuple: (new_log_file, new_log_date)
    """

    now = datetime.now()

    if now.date() != current_log_date:
        log_file.close()
        cleanup_old_logs(log_folder, log_retention_days)
        new_log_file = open(get_log_path(log_folder), "a")
        sys.stdout = Tee(sys.stdout, new_log_file)
        sys.stderr = Tee(sys.stderr, new_log_file)
        new_log_date = now.date()
        
        print(f"\nNew day detected — rotated log file for {now.strftime('%Y-%m-%d')}")
        return new_log_date, new_log_file
    
    return current_log_date, log_file




def show_disk_usage_bar(path: str = "/", bar_length: int = 40) -> None:
    """Display a simple disk usage bar for the given path."""
    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist.")
        return

    try:
        total, used, free = shutil.disk_usage(path)
    except PermissionError:
        print(f"Error: No permission to access '{path}'.")
        return

    used_percent = used / total if total > 0 else 0
    used_blocks = int(bar_length * used_percent)
    free_blocks = bar_length - used_blocks

    bar = "█" * used_blocks + "-" * free_blocks
    print(f"Path: {path}")
    print(f"[{bar}] {used_percent*100:.1f}% used")
    print(f"Total: {total / (1024**3):.2f} GB | Used: {used / (1024**3):.2f} GB | Free: {free / (1024**3):.2f} GB")
