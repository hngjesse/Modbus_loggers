from pymodbus.client import ModbusSerialClient
from datetime import datetime
import csv
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.common_utils import show_disk_usage_bar, get_log_path, cleanup_old_logs, Tee


# === Modbus connection setup ===
client = ModbusSerialClient(port="/dev/ttyS0", baudrate=19200, timeout=0.2, stopbits=1, bytesize=8)
client.connect()

START_ADDR = 0x0000
REG_COUNT = 40
TIME_STEP = 2  # seconds between each read cycle


LOG_RETENTION_DAYS = 30  # keep only last 30 days of log files

# === Logging setup ===
BASE_FOLDER = "/mnt/data_storage/Modbus_loggers/DC_meter_logger"
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)




def get_csv_path():
    """Return current CSV file path based on current year and month."""
    now = datetime.now()
    year_folder = os.path.join(BASE_FOLDER, "data", now.strftime("%Y"))
    month_name = now.strftime("%Y-%m")

    os.makedirs(year_folder, exist_ok=True)
    csv_path = os.path.join(year_folder, f"{month_name}_dc_meter_log.csv")

    if not os.path.exists(csv_path):
        with open(csv_path, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Datetime", "Device_ID", "Forward_energy_kWh",
                "Active_power_kW", "Current_A", "Voltage_V", "Error"
            ])
    return csv_path


# === Initialize logging ===
current_log_date = datetime.now().date()
log_file = open(get_log_path(LOG_FOLDER), "a")
sys.stdout = Tee(sys.stdout, log_file)
sys.stderr = Tee(sys.stderr, log_file)

print("Starting continuous Modbus data logging...\n(Press Ctrl+C to stop)\n")
cleanup_old_logs(LOG_FOLDER,LOG_RETENTION_DAYS)


# === Main loop ===
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

        for device_id in range(1, 9):
            print(f"\nReading DC meter (DCM3366) with Modbus ID = {device_id} ...")

            try:
                response = client.read_holding_registers(
                    address=START_ADDR, count=REG_COUNT, device_id=device_id
                )
            except Exception as e:
                print(f"Exception reading device {device_id}: {e}")
                Forward_energy = Active_power = Current = Voltage = None
                Error = "Error"
                now = datetime.now().isoformat()
                print(f"Datetime: {now}")
                print(f"Forward energy (kWh): {Forward_energy}")
                print(f"Active power (kW): {Active_power}")
                print(f"Current (A): {Current}")
                print(f"Voltage (V): {Voltage}")
                with open(CSV_FILE, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([now, device_id, Forward_energy, Active_power, Current, Voltage, Error])
                continue

            regs = response.registers
            print(f"Raw registers ({len(regs)}): {regs}")

            Forward_energy = (regs[0] << 16) + regs[1]
            Active_power = (regs[20] << 16) + regs[21]
            Current = (regs[22] << 16) + regs[23]
            Voltage = (regs[24] << 16) + regs[25]
            Error = "No error"
            now = datetime.now().isoformat()

            print(f"Datetime: {now}")
            print(f"Forward energy (kWh): {Forward_energy / 100:.3f}")
            print(f"Active power (kW): {Active_power / 1000:.3f}")
            print(f"Current (A): {Current / 10000:.3f}")
            print(f"Voltage (V): {Voltage / 10000:.1f}")
            with open(CSV_FILE, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    now,
                    device_id,
                    round(Forward_energy / 100, 3),
                    round(Active_power / 1000, 3),
                    round(Current / 10000, 3),
                    round(Voltage / 10000, 1),
                    Error
                ])
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