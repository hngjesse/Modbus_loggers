import os
import sys
import time
import importlib
import logging
from datetime import datetime
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from utils.validate_config import validate_config
from utils.common_utils import get_csv_path_daily, show_disk_usage_bar, get_log_path, cleanup_old_logs, log_rotation



# --- Verify command-line argument ---
if len(sys.argv) < 2:
    print("Usage: python modbus_logger.py <config_file.json>")
    sys.exit(1)

# --- Load the specified config file ---
CONFIG_PATH = sys.argv[1]
# --- Validate configuration ---
config = validate_config(CONFIG_PATH)



modbus_cfg = config["modbus"]
device_cfg = config["device"]
log_cfg = config["logging"]


# === Setup directories ===
BASE_FOLDER = log_cfg["base_folder"]
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)

# === Configure logger ===
log_path = get_log_path(LOG_FOLDER)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)


logger = logging.getLogger(__name__)
logger.info("[main] Starting Modbus Data Logger")
logger.info(f"[main] Using configuration file: {CONFIG_PATH}")
cleanup_old_logs(LOG_FOLDER, log_cfg["log_retention_days"])


# === Initialize Modbus client ===
try:
    if modbus_cfg["type"].lower() == "serial":
        client = ModbusSerialClient(
            port=modbus_cfg["port"],
            baudrate=modbus_cfg["baudrate"],
            timeout=modbus_cfg["timeout"],
            stopbits=modbus_cfg["stopbits"],
            bytesize=modbus_cfg["bytesize"],
            parity=modbus_cfg["parity"],
        )
    elif modbus_cfg["type"].lower() == "tcp":
        client = ModbusTcpClient(
            host=modbus_cfg["host"],
            port=modbus_cfg["port"],
            timeout=modbus_cfg["timeout"],
        )
    else:
        raise ValueError(f"Invalid connection type: {modbus_cfg['type']} (expected 'serial' or 'tcp')")
except Exception as e:
    logger.error(f"[main] Failed to initialize Modbus client: {e}")
    sys.exit(1)

# === Attempt connection ===
if not client.connect():
    logger.error("[main] Failed to connect to Modbus device. Will retry via systemd.")
    sys.exit(1)

logger.info("[main] Connected to Modbus device successfully.")





# === Dynamically import device-specific function ===
try:
    device_module = importlib.import_module("utils.device_specific_func")
    device_func = getattr(device_module, device_cfg["name"])
except (ImportError, AttributeError):
    logger.error(f"[main] Could not load device function '{device_cfg['name']}' from utils/device_specific_func.py")
    sys.exit(1)




# === Device parameters ===
START_ADDR = device_cfg["start_addr"]
REG_COUNT = device_cfg["reg_count"]
ID_RANGE = device_cfg["id_range"]


# === Logging parameters ===
LOG_RETENTION_DAYS = log_cfg["log_retention_days"]
FILE_SUFFIX = log_cfg["file_suffix"]
HEADER = log_cfg.get("header", [])
TIME_STEP = log_cfg["time_step"]

current_log_date = datetime.now().date()

# === Main loop ===
try:
    while True:
        now = datetime.now()

        # Rotate log daily
        current_log_date, new_log_path = log_rotation(LOG_FOLDER, current_log_date, LOG_RETENTION_DAYS)
        if new_log_path:
            for h in logger.handlers:
                if isinstance(h, logging.FileHandler):
                    h.baseFilename = new_log_path
                    logger.info(f"[main] Log file switched to: {new_log_path}")

        # Prepare CSV
        CSV_FILE = get_csv_path_daily(base_folder = BASE_FOLDER, file_suffix = FILE_SUFFIX, header = HEADER)

        # Show disk usage
        show_disk_usage_bar("/")
        show_disk_usage_bar("/mnt/data_storage")

        logger.info(f"[main] Waiting {TIME_STEP} seconds before next read cycle...")
        time.sleep(TIME_STEP)

        # Read Modbus data
        try:
            device_func(client, START_ADDR, REG_COUNT, CSV_FILE, ID_RANGE)
        except Exception as e:
            logger.error(f"[main] Error during Modbus read: {e}")

except KeyboardInterrupt:
    logger.info("[main] 🛑 Stopped by user (Ctrl+C).")
finally:
    client.close()
    logger.info("[main] ✅ Modbus client closed.")