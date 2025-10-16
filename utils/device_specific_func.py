from pymodbus.client import ModbusSerialClient
import struct
import csv
from datetime import datetime

def tp_700(client: ModbusSerialClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    for unit_id in device_range:
        print(f"\nReading temperature data logger (TP-700) with Modbus ID = {unit_id} ...")

        try:
            response = client.read_holding_registers(address=start_addr, count=reg_count, device_id=unit_id)
        except Exception as e:
            print(f"Exception reading device {unit_id}: {e}")
            temps = [None] * 24
            Error = "Error"
            now = datetime.now().isoformat()
            print(f"Datetime: {now}")
            for i in range(0, len(temps), 6):  # step by 6
                row = temps[i:i+6]
                print("  ".join(f"CH{i+j+1:02d}: {t}" for j, t in enumerate(row)))

            with open(csv_file, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, unit_id] + temps + [Error])
            continue

        regs = response.registers
        if not regs or len(regs) < reg_count:
            print(f"Incomplete response from device {unit_id}")
            continue

        print(f"Raw registers ({len(regs)}): {regs}")

        # === Decode 24 temperature channels (big endian) ===
        temps = []
        for i in range(0, reg_count, 2):
            high = regs[i]
            low = regs[i + 1]
            bytes_be = struct.pack('>HH', high, low)   # pack as big-endian 16-bit words
            temp_c = struct.unpack('>f', bytes_be)[0]  # unpack as 32-bit float BE
            temps.append(temp_c)
        Error = "No error"
        now = datetime.now().isoformat()
        print(f"Datetime: {now}")
        for i in range(0, len(temps), 6):  # step by 6
            row = temps[i:i+6]
            print("  ".join(f"CH{i+j+1:02d}: {t:.2f} °C" for j, t in enumerate(row)))

        # === Write to CSV ===
        with open(csv_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([now, unit_id] + [round(t, 2) for t in temps] + [Error])




def DCM_3366(client: ModbusSerialClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    for device_id in device_range:
        print(f"\nReading DC meter (DCM3366) with Modbus ID = {device_id} ...")

        try:
            response = client.read_holding_registers(
                address=start_addr, count=reg_count, device_id=device_id
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
            with open(csv_file, mode="a", newline="") as f:
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
        with open(csv_file, mode="a", newline="") as f:
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
