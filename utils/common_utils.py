import os
import shutil
import csv
import logging
from datetime import datetime, timedelta


def get_csv_path_daily(base_folder: str, file_suffix: str, header: list) -> str:
    """
    Create and return the CSV path for the current day, organized as:
        base_folder/data/YYYY/MM/YYYY-MM-DD_suffix.csv

    Args:
        base_folder (str): Base directory where the 'data' folder will be created.
        file_suffix (str): Short identifier for the file (e.g., "temp_log", "dc_meter").
        header (list): List of column headers for the CSV file.

    Returns:
        str: Full path to the CSV file.
    """
    now = datetime.now()
    
    # Folder hierarchy: data/YYYY/MM/
    year_folder = os.path.join(base_folder, "data", now.strftime("%Y"))
    month_folder = os.path.join(year_folder, now.strftime("%m"))
    os.makedirs(month_folder, exist_ok=True)

    # Daily file name: YYYY-MM-DD_suffix.csv
    day_name = now.strftime("%Y-%m-%d")
    csv_path = os.path.join(month_folder, f"{day_name}_{file_suffix}.csv")

    # Create CSV file with header if needed
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        with open(csv_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            if header:  # allow empty list, don't fail
                writer.writerow(header)
        logging.info(f"[csv] Created new CSV file: {csv_path}")

    return csv_path


def cleanup_old_logs(log_folder: str, log_retention_days: int) -> None:
    """
    Delete .log files in `log_folder` older than `log_retention_days`.
    """
    if not os.path.isdir(log_folder):
        logging.warning(f"[log] Log folder '{log_folder}' not found.")
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
                logging.info(f"[log] Deleted old log: {fname}")
                deleted_count += 1
        except ValueError:
            continue

    if deleted_count == 0:
        logging.info("[log] No old log files found to delete.")
    else:
        logging.info(f"[log] Deleted {deleted_count} old log file(s).")


def get_log_path(log_folder: str) -> str:
    """Return today's log file path, ensuring folder exists."""
    os.makedirs(log_folder, exist_ok=True)
    return os.path.join(log_folder, f"{datetime.now().strftime('%Y-%m-%d')}.log")


def log_rotation(log_folder: str, current_log_date, log_retention_days) -> tuple:
    """
    Checks if a new day has started; rotates log files automatically.

    Returns:
        tuple: (new_log_date, new_log_path)
    """
    now = datetime.now()

    if now.date() != current_log_date:
        cleanup_old_logs(log_folder, log_retention_days)
        new_log_path = get_log_path(log_folder)
        logging.info(f"[log] New day detected — rotated log file for {now.strftime('%Y-%m-%d')}")
        return now.date(), new_log_path

    return current_log_date, None


def show_disk_usage_bar(path: str = "/", bar_length: int = 40) -> None:
    """Display a simple disk usage bar for the given path."""
    if not os.path.exists(path):
        logging.error(f"[disk] Path '{path}' does not exist.")
        return

    try:
        total, used, free = shutil.disk_usage(path)
    except PermissionError:
        logging.error(f"[disk] No permission to access '{path}'.")
        return

    used_percent = used / total if total > 0 else 0
    used_blocks = int(bar_length * used_percent)
    free_blocks = bar_length - used_blocks

    bar = "█" * used_blocks + "-" * free_blocks
    logging.info(f"[disk] Path: {path}")
    logging.info(
        f"[disk] [{bar}] {used_percent*100:.1f}% "
        f"Total: {total / (1024**3):.2f} GB | Used: {used / (1024**3):.2f} GB | Free: {free / (1024**3):.2f} GB"
    )