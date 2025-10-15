
# Modbus-based Data Logger

This project is a **Python-based Modbus data logger** designed to read and record device's data from DCM 3366 DC meter connected via RS-485. It runs continuously on a **Linux-based mini PC (ECS-1841)** and automatically logs readings into daily `.log` files and monthly `.csv` files.

---

## Features

- Continuous data logging
- Automatic daily log rotation 
- Monthly CSV exportation
- 30-day retention policy — old logs are deleted automatically  
- Handles communication errors gracefully  
- Runs continuously (can be deployed as a `systemd` service)
- Include disks usage update


---

## File Structure

```
/mnt/data_storage/Modbus_loggers/
DC_meter_logger/
│   ├── dc_meter_logger.py
│   ├── logs/
│   │   ├── 2025-10-11.log
│   │   ├── 2025-10-12.log
│   │   └── ...
│   ├── data/
│       ├── 2025/
│       │   ├── 2025-10_dc_meter_log.csv
│       │   ├── 2025-11_dc_meter_log.csv
│       │   └── ...
│       ├──2026/
│       │   ├── 2025-10_dc_meter_log.csv
│       │   ├── 2025-11_dc_meter_log.csv
│       │   └── ...
│       └── ...
Temp_logger/
│   ├── temp_logger.py
│   ├── logs/
│   │   ├── 2025-10-11.log
│   │   ├── 2025-10-12.log
│   │   └── ...
│   ├── data/
│       ├── 2025/
│       │   ├── 2025-10_temp_log.csv
│       │   ├── 2025-11_temp_log.csv
│       │   └── ...
│       ├──2026/
│       │   ├── 2025-10_temp_log.csv
│       │   ├── 2025-11_temp_log.csv
│       │   └── ...
│       └── ...
utils/
    ├── __init__.py
    └── common_utils.py
```

---

## Running the Script

### Prerequisites
- Python 3.8+  
- `pymodbus` library installed  

```bash
pip install pymodbus
```

### Run the script manually
```bash
python x_logger.py
```
### Run as a background service

- Create a systemd service

```bash
sudo nano /etc/systemd/system/x_logger.service
```

- Then we add the following task for linux to automate.

```
[Unit]
Description=X Data Logger
After=network.target

[Service]
Type=simple
User=utar-mini-pc
WorkingDirectory=/mnt/data_storage/Modbus_loggers/X_logger/scripting
ExecStart=/home/utar-mini-pc/anaconda3/envs/utar_py/bin/python x_logger.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

- Enable and start it

```bash
sudo systemctl enable x_logger.service
sudo systemctl start x_logger.service
```

### Status of `x_logger.service`
```bash
sudo systemctl status x_logger.service
```

### Tail the log
```bash
journalctl -u x_logger.service -f
```

---

## Remove it from background service
To remove a service from system completely, do the following.

### Stop service
```bash
sudo systemctl stop x_logger.service
```
### Disable it (remove system link)

```bash
sudo systemctl disable x_logger.service
```

### Remove the service file

```bash
sudo rm /etc/systemd/system/x_logger.service
```
### Reload the systemd daemon

```bash
sudo systemctl daemon-reload
```

### Verify that it has been removed

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

- Older logs beyond 30 days are deleted automatically

---
## Data Colelction

- All collected data by `x_logger.py` will be saved to `data/data/YYYY/YYYY-MM_x_log.csv`

---

## Notes

- Update the Modbus device ID range in the code if you have more devices:
```python
    for device_id in range(1, 9):
```
- Adjust the TIME_STEP (currently 2 seconds) for your preferred polling interval.

---

# Git Cheat Sheet

## Navigate to your project folder
```bash
cd /mnt/data_storage/X_logger
```

## Initialize a Git repository (only once)
```bash
git init
```

## Change from master to main
```bash
git branch -m main
```

## Add your GitHub remote
```bash
git remote add origin https://github.com/<your_username>/X_logger.git
```

## Create a .gitignore file
```bash
nano .gitignore
```

## Paste the following lines
```
*.log
*.csv
__pycache__/
*.pyc
.env
*.tmp
```

## Stage and commit all your files
```bash
git add .
git commit -m "Initial commit: Modbus logger scripts"
```

## Push to GitHub
```bash
git branch -M main
git push -u origin main
```

## For future updates
```bash
git add .
git commit -m "Updated decoding and service config"
git push
```
---

## To clone this repo on another computer
```bash
git clone https://github.com/<your_username>/X_logger.git
```


## License

This project is intended for internal use in DC meter monitoring systems.
All rights reserved © 2025.