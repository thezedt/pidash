# PiDash
**Pi Dash(board) for HomeAssistant**

A dashboard for displaying sensor data on a Waveshare 1.44-inch LCD HAT (model 13891).

---

## File Structure

| File | Purpose |
|------|---------|
| `dashboard.py` | **Main wrapper**: Polls Home Assistant, handles buttons, renders to LCD |
| `dash_config.py` | **HA API credentials** (uses `HA_URL`/`HA_TOKEN` env vars) |
| `dash_setup.py` | **Hardware setup**: Sensors, GPIO pins, LCD/backlight setup, colors |
| `dash_functions.py` | **Core logic**: HA API client, rendering, button events, menu state |
| `dash_helpers.py` | **Utilities**: Color helpers, text formatting, icon drawing |
| `dash_screens.py` | **Screen layouts**: Solar, Temps, Params, EV, Energy |

---

## Key Features

### 5 Data Screens
- **Solar**: Power flow (solar -> grid/house/battery)
- **Temps**: Temperature/humidity sensors (10+ locations)
- **Params**: Inverter/battery parameters (temps, limits, power)
- **Spring**: EV charging data (battery %, power, time remaining)
- **Energy**: Daily cumulative energy (solar/grid/house/battery)

### Navigation
- **Joystick**: Up/Down/Left/Right cycles through all 5 screens while on them; Middle Joystick opens the configuration menu (up/down cycles through the items while right joystick enters/toggles)
- **Shortcut buttons**: Key1-Top (Temps), Key2-Middle (Params), Key3-bottom (Spring)
- **Menu combo**: Hold Key1 + Key3 to (also) open menu
- **Idle timeout**: Returns to screen 1 after 60s inactivity

### Hardware
- **Display**: Waveshare 1.44" LCD (ST7735, 128x128)
- **Backlight**: PWM-controlled (day/night brightness)
- **Buttons**: 8 inputs (joystick + 3 keys)
- **Dependencies**: `luma.lcd`, `RPi.GPIO`, `pigpio`, `Pillow`

### Home Assistant Integration
- Reads **40+ sensors** in a single API call (`/api/states`)
- Background threading for non-blocking updates
- Handles network errors (shows broken Wi-Fi icon and semi-diagnostic error messages)
- Test mode with random data (toggle via hidden menu)

### Visual Feedback
- Color-coded values (red/green/blue for thresholds)
- Icons for solar, grid, house, battery, fans, thermometer
- Inverter off-grid alert (red background)
- Loading spinner during actions (restart, shutdown)

---

## How to Use This Code

> [!WARNING]
> **Note**: This code is **seriously** hardcoded for my specific setup, sensors configuration and IDs, devices and requirements. Will require extensive configuration, adjusting and testing to fit your usage case._

### Hardware Setup
1. Enable SPI and I2C on Raspberry Pi:
   ```bash
   sudo raspi-config
   ```
2. Install dependencies:
   ```bash
   sudo apt install python3-pip python3-pigpio fonts-dejavu-core fonts-dejavu-extra
   pip3 install luma.lcd RPi.GPIO pillow requests
   ```
3. Start `pigpiod` for PWM backlight:
   ```bash
   sudo systemctl enable --now pigpiod
   ```

### Configuration
Set Home Assistant URL and token in `dash_config.py` directly:
```bash
HA_URL = os.getenv("HA_URL", "http://REDACTED:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "REDACTED")
```
Also define your local network CIDR for correctly identifying connected state (in the same `dash_config.py` file):
```bash
REQUIRED_NETWORK = ipaddress.ip_network("192.168.1.0/24")
```


### Run the Dashboard to test
```bash
cd /path/to/pidash
python3 dashboard.py
```

### Run as a Service
Create `/etc/systemd/system/dashboard.service`:
```ini
[Unit]
Description=PiDash Dashboard
After=pigpiod.service
Requires=pigpiod.service

[Service]
ExecStart=/usr/bin/python3 /path/to/pidash/dashboard.py
WorkingDirectory=/path/to/pidash
Restart=always

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl enable --now dashboard.service
```

---
