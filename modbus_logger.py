from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from datetime import datetime
import os
import time
import sys
import json
import importlib
from utils.common_utils import get_csv_path_daily, show_disk_usage_bar, get_log_path, cleanup_old_logs, log_rotation, Tee
from utils.validate_config import validate_config


# --- Check that a config file was provided ---
if len(sys.argv) < 2:
    print("Usage: python modbus_logger.py <config_file.json>")
    sys.exit(1)

# --- Load the specified config file ---
CONFIG_PATH = sys.argv[1]

# --- Validate configuration ---
config = validate_config(CONFIG_PATH)

with open(CONFIG_PATH) as f:
    config = json.load(f)


modbus_cfg = config["modbus"]
device_cfg = config["device"]
log_cfg = config["logging"]



if modbus_cfg["type"].lower() == "serial":
    client = ModbusSerialClient(
        port=modbus_cfg["port"],
        baudrate=modbus_cfg["baudrate"],
        timeout=modbus_cfg["timeout"],
        stopbits=modbus_cfg["stopbits"],
        bytesize=modbus_cfg["bytesize"],
        parity=modbus_cfg["parity"]
    )
elif modbus_cfg["type"].lower() == "tcp":
    client = ModbusTcpClient(
        host=modbus_cfg["host"],
        port=modbus_cfg["port"],
        timeout=modbus_cfg["timeout"]
    )
else:
    raise ValueError(f"Invalid connection type: {modbus_cfg['type']} (expected 'serial' or 'tcp')")


client.connect()


# === Dynamically import device-specific function ===
device_name = device_cfg["name"]
device_module = importlib.import_module("utils.device_specific_func")
device_func = getattr(device_module, device_name)

# === Device parameters ===
START_ADDR = device_cfg["start_addr"]
REG_COUNT = device_cfg["reg_count"]
ID_RANGE = device_cfg["id_range"]  # e.g., [1, 10] for IDs 1 to 10

# === Logging parameters ===
BASE_FOLDER = log_cfg["base_folder"]
LOG_RETENTION_DAYS = log_cfg["log_retention_days"]
FILE_SUFFIX = log_cfg["file_suffix"]
TIME_STEP = log_cfg["time_step"]
HEADER = log_cfg["header"]


# === Prepare log folder ===
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)


# === Initialize logging ===
current_log_date = datetime.now().date()
log_file = open(get_log_path(LOG_FOLDER), "a")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

print("Starting continuous logging...\n(Press Ctrl+C to stop)\n")
cleanup_old_logs(LOG_FOLDER,LOG_RETENTION_DAYS)



# === Connect client ===
if not client.connect():
    print(f"{datetime.now().isoformat()} ❌ Failed to connect to Modbus device.")
    log_file.close()
    sys.exit(1)
else:
    print("✅ Connected to Modbus device.")

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
        device_func(client, START_ADDR, REG_COUNT, CSV_FILE, ID_RANGE)


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
