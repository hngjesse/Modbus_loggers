
# Modbus-based Data Logger

This project is a **Python-based Modbus data logger** designed to read and record device's data from multiple Modbus-compatible devices using either Modbus RTU (Serial) or Modbus TCP. It runs continuously on a **Linux-based mini PC (ECS-1841)** and automatically logs readings into daily `.log` and `.csv` files.

---

## Features

- A single reusable script `modbus_logger.py` that supports multiple devices via configuration files.
- Device-specific logic modularized under `utils/device_specific_func.py`
- Fully configurable setup via **JSON**, no hardcoded parameters.
- Supports both **Serial (RS485)** and **TCP** Modbus connections.
- Automatic daily CSV rotation and log cleanup.
- Background execution via `systemd`.
- Centralized utilities under `utils/` (e.g. logging, validation, and disk monitoring).
- Automatic configuration validation via `utils/validate_config.py`.


---

## File Structure

```
/mnt/data_storage/Modbus_loggers/
│
├── modbus_logger.py
│
├── configs/
│   ├── tp_700_conf.json
│   ├── dcm_3366_conf.json
│   └── hoymile_dtu_pro_conf.json
│
├── utils/
│   ├── __init__.py
│   ├── common_utils.py
│   ├── device_specific_func.py
│   └── validate_config.py
│
├── logs/
│   ├── 2025-10-18.log
│   ├── 2025-10-19.log
│   └── ...
│
├── data/
│   ├── 2025/
│   │   ├── 10/
│   │   │   ├── 2025-10-18_temp.csv
│   │   │   ├── 2025-10-18_dc_meter.csv
│   │   │   └── ...
│   │   └── 11/
│   │       └── ...
│   └── 2026/
│       └── ...
│
└── README.md
```

---

## JSON configuration file
All device and communication settings are now handled in `.json` configuration files inside `/configs`.

### Example (Modbus TCP)
```json
{
  "modbus": {
    "type": "tcp",
    "timeout": 0.2,
    "host": "192.168.1.10",
    "port": 502
  },
  "device": {
    "name": "tp_700",
    "start_addr": 4097,
    "reg_count": 48,
    "id_range": [1, 1]
  },
  "logging": {
    "base_folder": "/mnt/data_storage/Modbus_loggers/data/temp_logger",
    "log_retention_days": 30,
    "file_suffix": "temp",
    "header": ["Datetime", "Device_ID", "CH1_Temp", "CH2_Temp", "CH3_Temp", "Error"],
    "time_step": 2
  }
}
```

### Example (Modbus RTU)
```json
{
  "modbus": {
    "type": "serial",
    "port": "/dev/ttyS0",
    "baudrate": 19200,
    "timeout": 0.2,
    "stopbits": 1,
    "bytesize": 8,
    "parity": "N"
  },
  "device": {
    "name": "dcm_3366",
    "start_addr": 0,
    "reg_count": 40,
    "id_range": [1,2,3,4,5,6,7,8]
  },
  "logging": {
    "base_folder": "/mnt/data_storage/Modbus_loggers/data/dcm_3366",
    "log_retention_days": 30,
    "file_suffix": "dc_meter",
    "header": ["Datetime", "Device_ID", "Forward_energy_kWh", "Active_power_kW", "Current_A", "Voltage_V", "Error"],
    "time_step": 2
  }
}
```





## Running the Script

### Prerequisites
- Python 3.8+  
- `pymodbus` (≥ 3.11.3)

```bash
pip install pymodbus
```

### Run the script manually
```bash
python modbus_logger.py configs/x_conf.json
```
### Run as a background service

- Create a systemd service

```bash
sudo nano /etc/systemd/system/x_logger.service
```

- Then paste the following configuration.

```bash
[Unit]
Description=X Data Logger
After=network.target

[Service]
Type=simple
User=utar-mini-pc
WorkingDirectory=/mnt/data_storage/Modbus_loggers
ExecStart=/home/utar-mini-pc/anaconda3/envs/utar_py/bin/python modbus_logger.py configs/x_conf.json
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

- Enable and start the service

```bash
sudo systemctl enable x_logger.service
sudo systemctl start x_logger.service
```

- Check status of `x_logger.service`
```bash
sudo systemctl status x_logger.service
```

- Tail the log
```bash
journalctl -u x_logger.service -f
```

- Stop and remove the service
```bash
sudo systemctl stop x_logger.service
sudo systemctl disable x_logger.service
sudo rm /etc/systemd/system/x_logger.service
sudo systemctl daemon-reload
```

- Verify that it has been removed
```bash
systemctl status x_logger.service
```

---

## Permissions

- Make sure your user has access to the serial port
```bash
sudo usermod -a -G dialout user
```

---

## Log Rotation & Retention

- Logs are saved daily in `logs/YYYY-MM-DD.log`

- Older logs beyond the retention period (default: 30 days) are automatically deleted

---
## Data Colelction

- All collected data are stored in `data_storage`

---

## Notes

- Update the **JSON** config to change Modbus type, port, address range, or logging paths.
- To adjust polling rate, edit `"time_step"` in the config file.
- Each device can have its own independent config and `systemd` service for parallel data logging.

---

# Git Cheat Sheet

---

## Initialize and Push
```bash
cd /mnt/data_storage/Modbus_loggers
git init
git branch -m main
git remote add origin https://github.com/hngjesse/Modbus_loggers.git
git add .
git commit -m "Initial commit: Modbus logger with JSON config"
git push -u origin main
```

---

## Update repo
```bash
git add .
git commit -m "Updated configuration handling and utils"
git push
```

---

## Create a .gitignore file
```bash
nano .gitignore
```
## Paste the following lines
```
# Ignore system & editor files
__pycache__/
*.pyc
*.pyo
*.DS_Store
.vscode/
.idea/

# Ignore local data and logs
data_storage/
*.csv
*.log

# Ignore virtual environments
venv/
.env/

# Ignore temporary configs (if any)
*.bak
```

---

## To clone this repo on another computer
```bash
git clone https://github.com/hngjesse/Modbus_loggers.git
```

---

## License

This project is intended for internal use in industrial and solar monitoring systems.
All rights reserved © 2025 — Hng Jesse.