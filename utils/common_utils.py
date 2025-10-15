import os
from datetime import datetime, timedelta
import shutil


class Tee:
    """Duplicate terminal output to both stdout and a log file."""
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()



def cleanup_old_logs(log_folder, log_retention_days):
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
            date_str = fname[:-4]  # more efficient than replace
            fdate = datetime.strptime(date_str, "%Y-%m-%d")

            if fdate < cutoff:
                os.remove(fpath)
                print(f"🗑️ Deleted old log: {fname}")
                deleted_count += 1

        except ValueError:
            # Skip files not following YYYY-MM-DD.log format
            continue

    if deleted_count == 0:
        print("No old log files found to delete.")
    else:
        print(f"Deleted {deleted_count} old log file(s).")




def get_log_path(log_folder):
    """Return today's log file path, ensuring folder exists."""
    os.makedirs(log_folder, exist_ok=True)
    return os.path.join(log_folder, f"{datetime.now().strftime('%Y-%m-%d')}.log")




def show_disk_usage_bar(path="/", bar_length=40):
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