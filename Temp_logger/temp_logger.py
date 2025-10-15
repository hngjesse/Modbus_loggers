from pymodbus.client import ModbusSerialClient
from datetime import datetime, timedelta
import csv
import os
import time
import sys
import struct
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common_utils import show_disk_usage_bar, get_log_path, cleanup_old_logs, Tee

# === Modbus connection setup ===
client = ModbusSerialClient(port="/dev/ttyS3", baudrate=9600, timeout=0.2, stopbits=1, bytesize=8)
client.connect()

# === Settings ===
START_ADDR = 0x0000
REG_COUNT = 48           # 24 channels × 2 registers each
TIME_STEP = 2            # seconds between each read


LOG_RETENTION_DAYS = 30

BASE_FOLDER = "/mnt/data_storage/Modbus_loggers/Temp_logger"
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)


# === Helper function for CSV path ===
def get_csv_path():
    now = datetime.now()
    year_folder = os.path.join(BASE_FOLDER, "data", now.strftime("%Y"))
    month_name = now.strftime("%Y-%m")  # e.g. 2025-10
    os.makedirs(year_folder, exist_ok=True)
    csv_path = os.path.join(year_folder, f"{month_name}_temp_log.csv")

    # Create file with header if new
    if not os.path.exists(csv_path):
        with open(csv_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            header = ["Datetime", "Device_ID"] + [f"CH{i+1}_Temp" for i in range(24)] + ["Error"]
            writer.writerow(header)
    return csv_path


# === Initialize logging ===
current_log_date = datetime.now().date()
log_file = open(get_log_path(LOG_FOLDER), "a")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)




print("Starting continuous temperature logging...\n(Press Ctrl+C to stop)\n")
cleanup_old_logs(LOG_FOLDER,LOG_RETENTION_DAYS)

try:
    while True:
        now = datetime.now()

        # Check for log rotation (new day)
        if now.date() != current_log_date:
            log_file.close()
            cleanup_old_logs(LOG_FOLDER,LOG_RETENTION_DAYS)
            log_file = open(get_log_path(LOG_FOLDER), "a")
            sys.stdout = Tee(sys.stdout, log_file)
            sys.stderr = Tee(sys.stderr, log_file)
            current_log_date = now.date()
            print(f"\nNew day detected — rotated log file for {now.strftime('%Y-%m-%d')}")

        CSV_FILE = get_csv_path()

        # Adjust for your actual Modbus ID range
        for device_id in range(1, 2):
            print(f"\nReading temperature data logger (TP-700) with Modbus ID = {device_id} ...")

            try:
                response = client.read_holding_registers(address=START_ADDR, count=REG_COUNT, device_id=device_id)
            except Exception as e:
                now = datetime.now().isoformat()
                print(f"Exception reading device {device_id}: {e}")
                with open(CSV_FILE, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([now, device_id] + ["Error"] * 24 + ["Comm Error"])
                continue

            regs = response.registers
            if not regs or len(regs) < REG_COUNT:
                print(f"Incomplete response from device {device_id}")
                continue

            print(f"Raw registers ({len(regs)}): {regs}")

            # === Decode 24 temperature channels (big endian) ===
            temps = []
            for i in range(0, REG_COUNT, 2):
                high = regs[i]
                low = regs[i + 1]
                bytes_be = struct.pack('>HH', high, low)   # pack as big-endian 16-bit words
                temp_c = struct.unpack('>f', bytes_be)[0]  # unpack as 32-bit float BE
                temps.append(temp_c)

            now = datetime.now().isoformat()
            print(f"Datetime: {now}")
            for idx, t in enumerate(temps, start=1):
                print(f"CH{idx:02d}: {t:.2f} °C")
            

            # === Write to CSV ===
            with open(CSV_FILE, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, device_id] + [round(t, 2) for t in temps] + ["No error"])

        show_disk_usage_bar("/")
        show_disk_usage_bar("/mnt/data_storage")
        print(f"\n--- Waiting {TIME_STEP} seconds before next read cycle ---\n")
        time.sleep(TIME_STEP)

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
    