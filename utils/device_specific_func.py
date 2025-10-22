import struct
import csv
import logging
import time
from datetime import datetime
from pymodbus.client import ModbusSerialClient, ModbusTcpClient

logger = logging.getLogger(__name__)



def list_regis(client: ModbusSerialClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    """List and optionally save Modbus holding registers for one or more devices."""
    for unit_id in device_range:
        logger.info(f"[list_regis] Listing registers for device with Modbus ID = {unit_id} ...")

        try:
            response = client.read_holding_registers(address=start_addr, count=reg_count, device_id=unit_id)
            if not response or getattr(response, "isError", lambda: True)():
                logger.warning(f"[list_regis] No valid response from device {unit_id}")
                continue

            regs = response.registers
            if not regs:
                logger.warning(f"[list_regis] Incomplete response from device {unit_id}")
                continue

            logger.info(f"[list_regis] Raw registers ({len(regs)}):")

            chunk_size = 10  # how many registers per line
            for i in range(0, len(regs), chunk_size):
                chunk = regs[i:i + chunk_size]
                logger.info("[list_regis] [" + ", ".join(f"{r}" for r in chunk) + "]")

        except Exception as e:
            logger.error(f"[list_regis] Exception reading device {unit_id}: {e}")




def hoymiles_dtu_p(client: ModbusTcpClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    regs_even = []
    regs_odd = []

    for i in device_range:
        try:
            # Read even registers
            logger.info(f"[hoymiles_dtu_p] Collecting registers for device {i} ...")
            response_even = client.read_holding_registers(address=start_addr + 40 * (i - 1), count=reg_count, device_id=1)
            time.sleep(0.2)
            # Read odd registers
            response_odd = client.read_holding_registers(address=start_addr + 1 + 40 * (i - 1), count=reg_count, device_id=1)
            
            # Validate both responses
            if response_even.isError() or response_odd.isError():
                raise ValueError("Modbus read error detected")

            regs_even.append(response_even.registers + [datetime.now().strftime("%Y-%m-%dT%H:%M:%S")])
            regs_odd.append(response_odd.registers + [datetime.now().strftime("%Y-%m-%dT%H:%M:%S")])

            time.sleep(0.2)

        except Exception as e:
            logger.error(f"[hoymiles_dtu_p] Failed to read registers: {e}")
            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            with open(csv_file, mode="a", newline="") as f:
                csv.writer(f).writerow([now, f"Device {i}", None, None, None, None, None, None, None, None, None, "Read error"])
            continue

    # Parse collected data
    for i in device_range:
        try:
            chunk_size = 11  # how many registers per line
            logger.info(f"[tp_700] Raw even registers ({len(regs_even[i-1])}):")

            for j in range(0, len(regs_even[i-1]), chunk_size):
                chunk = regs_even[i-1][j:j + chunk_size]
                logger.info("[tp_700] [" + ", ".join(f"{r}" for r in chunk) + "]")

            logger.info(f"[tp_700] Raw even registers ({len(regs_odd[i-1])}):")
            for j in range(0, len(regs_odd[i-1]), chunk_size):
                chunk = regs_even[i-1][j:j + chunk_size]
                logger.info("[tp_700] [" + ", ".join(f"{r}" for r in chunk) + "]")
            
            now = regs_even[i - 1][20]
            serial_number = b''.join(struct.pack('>H', r) for r in regs_odd[i - 1][0:4]).hex()
            pv_voltage = regs_even[i - 1][4] / 10
            pv_current = regs_even[i - 1][5] / 100
            grid_voltage = regs_even[i - 1][6] / 10
            grid_freq = regs_even[i - 1][7] / 100
            pv_power = regs_even[i - 1][8] / 10
            today_prod = regs_even[i - 1][9]
            total_prod = None
            temperature = regs_even[i - 1][12] / 10
            operating_status1 = regs_even[i - 1][13]
            Error = "No error"

            logger.info(f"[hoymiles_dtu_p] Datetime         : {now}")
            logger.info(f"[hoymiles_dtu_p] Serial Number    : {serial_number}")
            logger.info(f"[hoymiles_dtu_p] PV Voltage [V]   : {pv_voltage}")
            logger.info(f"[hoymiles_dtu_p] PV Current [A]   : {pv_current}")
            logger.info(f"[hoymiles_dtu_p] PV Power [W]     : {pv_power}")
            logger.info(f"[hoymiles_dtu_p] Temp [°C]        : {temperature}")
            logger.info(f"[hoymiles_dtu_p] Operating Status : {operating_status1}")

            with open(csv_file, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    now, serial_number,
                    round(pv_voltage, 3),
                    round(pv_current, 3),
                    round(pv_power, 3),
                    round(temperature, 3),
                    round(grid_voltage, 3),
                    round(grid_freq, 3),
                    round(today_prod, 3),
                    total_prod,
                    operating_status1,
                    Error
                ])

        except IndexError as e:
            logger.error(f"[hoymiles_dtu_p] Index error while parsing data: {e}")
        except Exception as e:
            logger.error(f"[hoymiles_dtu_p] Unexpected error during parsing: {e}")




def tp_700(client: ModbusSerialClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    for unit_id in device_range:
        logger.info(f"[tp_700] Reading temperature data logger (TP-700) with Modbus ID = {unit_id} ...")

        try:
            response = client.read_holding_registers(address=start_addr, count=reg_count, device_id=unit_id)
        except Exception as e:
            logger.info(f"[tp_700] Exception reading device {unit_id}: {e}")
            temps = [None] * 24
            Error = "Error"
            now = datetime.now().isoformat()
            logger.info(f"[tp_700] Datetime: {now}")
            for i in range(0, len(temps), 6):  # step by 6
                row = temps[i:i+6]
                logger.info("[tp_700] " + "  ".join(f"CH{i+j+1:02d}: {t}" for j, t in enumerate(row)))

            with open(csv_file, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, unit_id] + temps + [Error])
            continue

        regs = response.registers
        if not regs or len(regs) < reg_count:
            logger.info(f"[tp_700] Incomplete response from device {unit_id}")
            continue


        logger.info(f"[tp_700] Raw registers ({len(regs)}):")

        chunk_size = 10  # how many registers per line
        for i in range(0, len(regs), chunk_size):
            chunk = regs[i:i + chunk_size]
            logger.info("[tp_700] [" + ", ".join(f"{r}" for r in chunk) + "]")




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
        logger.info(f"[tp_700] Datetime: {now}")
        for i in range(0, len(temps), 6):  # step by 6
            row = temps[i:i+6]
            logger.info("[tp_700] " + "  ".join(f"CH{i+j+1:02d}: {t:.2f} °C" for j, t in enumerate(row)))

        # === Write to CSV ===
        with open(csv_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([now, unit_id] + [round(t, 2) for t in temps] + [Error])


def dcm_3366(client: ModbusSerialClient, start_addr: int, reg_count: int, csv_file: str, device_range: range) -> None:
    """Read DC meter (DCM3366) and save readings."""
    for device_id in device_range:
        logger.info(f"[dcm_3366] Reading DC meter (DCM3366) with Modbus ID = {device_id} ...")

        try:
            response = client.read_holding_registers(
                address=start_addr, count=reg_count, device_id=device_id
            )
        except Exception as e:
            logger.info(f"[dcm_3366] Exception reading device {device_id}: {e}")
            Forward_energy = Active_power = Current = Voltage = None
            Error = "Error"
            now = datetime.now().isoformat()
            logger.info(f"[dcm_3366] Datetime: {now}")
            logger.info(f"[dcm_3366] Forward energy (kWh): {Forward_energy}")
            logger.info(f"[dcm_3366] Active power (kW): {Active_power}")
            logger.info(f"[dcm_3366] Current (A): {Current}")
            logger.info(f"[dcm_3366] Voltage (V): {Voltage}")
            with open(csv_file, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([now, device_id, Forward_energy, Active_power, Current, Voltage, Error])
            continue

        regs = response.registers

        # Pretty-print raw register values in multiple lines

        logger.info(f"[dcm_3366] Raw registers ({len(regs)}):")

        chunk_size = 20  # how many registers per line
        for i in range(0, len(regs), chunk_size):
            chunk = regs[i:i + chunk_size]
            logger.info("[dcm_3366] [" + ", ".join(f"{r}" for r in chunk) + "]")


        Forward_energy = (regs[0] << 16) + regs[1]
        Active_power = (regs[20] << 16) + regs[21]
        Current = (regs[22] << 16) + regs[23]
        Voltage = (regs[24] << 16) + regs[25]
        Error = "No error"
        now = datetime.now().isoformat()

        logger.info(f"[dcm_3366] Datetime: {now}")
        logger.info(f"[dcm_3366] Forward energy (kWh): {Forward_energy / 100:.3f}")
        logger.info(f"[dcm_3366] Active power (kW): {Active_power / 1000:.3f}")
        logger.info(f"[dcm_3366] Current (A): {Current / 10000:.3f}")
        logger.info(f"[dcm_3366] Voltage (V): {Voltage / 10000:.1f}")
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
