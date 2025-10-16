from pymodbus.client import ModbusSerialClient
from datetime import datetime
import os
import time
import sys
# === Add parent directory to sys.path for imports ===
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# === Import self-defined common utilities ===
from utils.common_utils import get_csv_path_daily, show_disk_usage_bar, get_log_path, cleanup_old_logs, log_rotation, Tee
from utils.device_specific_func import DCM_3366




# === Modbus connection setup ===
client = ModbusSerialClient(port="/dev/ttyS0", baudrate=19200, timeout=0.2, stopbits=1, bytesize=8)
client.connect()

# === Settings ===
START_ADDR = 0x0000
REG_COUNT = 40
TIME_STEP = 2  # seconds between each read cycle


LOG_RETENTION_DAYS = 30  # keep only last 30 days of log files

BASE_FOLDER = "/mnt/data_storage/Modbus_loggers/DC_meter_logger"
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")

FILE_SUFFIX = "dc_meter"
HEADER = ["Datetime", "Device_ID", "Forward_energy_kWh", "Active_power_kW", "Current_A", "Voltage_V", "Error"]


os.makedirs(LOG_FOLDER, exist_ok=True)


# === Initialize logging ===
current_log_date = datetime.now().date()
log_file = open(get_log_path(LOG_FOLDER), "a")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

print("Starting continuous DC meter data logging...\n(Press Ctrl+C to stop)\n")
cleanup_old_logs(LOG_FOLDER,LOG_RETENTION_DAYS)


# === Main loop ===
try:
    while True:
        now = datetime.now()

        # Check for log rotation (new day)
        current_log_date, log_file = log_rotation(LOG_FOLDER, log_file, current_log_date, LOG_RETENTION_DAYS)

        CSV_FILE = get_csv_path_daily(base_folder = BASE_FOLDER, file_suffix = FILE_SUFFIX, header = HEADER)

        show_disk_usage_bar("/")
        show_disk_usage_bar("/mnt/data_storage")
        print(f"\n--- Waiting {TIME_STEP} seconds before next read cycle ---\n")
        time.sleep(TIME_STEP)

        # Adjust for your actual Modbus ID range
        DCM_3366(client, START_ADDR, REG_COUNT, CSV_FILE, range(1, 9))


except KeyboardInterrupt:
    print("\n🛑 Stopped by user (Ctrl+C). Closing connection...")
finally:
    client.close()          # always close Modbus client first
    try:
        print("✅ Modbus client closed.")
    except ValueError:
        # stdout/stderr already closed
        pass
    log_file.close()        # close the log file last