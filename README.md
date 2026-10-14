# PiDash
**Pi Dash(board) for HomeAssistant**

A dashboard for displaying sensor data on a [Waveshare 1.44-inch LCD HAT (model 13891)](https://www.waveshare.com/1.44inch-lcd-hat.htm).

![Dashboard Solar Screen](/assets/dashboard.jpg)

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
| `dash_translation.py` | **Translatable strings**: All front-facing texts displayed on-screen |

---

## Key Features

### 5 Data Screens
- **Solar**: Power flow (solar -> grid/house/battery)
- **Temps**: Temperature/humidity sensors (10+ locations)
- **Params**: Inverter/battery parameters (temps, limits, power)
- **EV**: EV charging data (battery %, power, time remaining)
- **Energy**: Daily cumulative energy (solar/grid/house/battery)

### Navigation
- **Joystick**: Up/Down/Left/Right cycles through all 5 screens while on them; Middle Joystick opens the configuration menu (up/down cycles through the items while right joystick enters/toggles)
- **Shortcut buttons**: Key1-Top (Temps), Key2-Middle (Params), Key3-bottom (EV)
- **Menu combo**: Hold Key1 + Key3 to (also) open menu
- **Idle timeout**: Returns to screen 1 after 60s inactivity

### Hardware
- **Workhorse**: Raspberry Pi - a Zero Wireless will do fine 
- **Display**: Waveshare 1.44" LCD (ST7735, 128x128)
- **Backlight**: PWM-controlled (day/night brightness)
- **Buttons**: 8 inputs (4 axis joystick with middle button + 3 separate keys)
- **Dependencies**: `luma.lcd`, `RPi.GPIO`, `pigpio`, `Pillow`

![The Hardware](/assets/hardware.jpg)

### Home Assistant Integration
- Reads **40+ sensors** in a single API call (`/api/states`)
- Background threading for non-blocking updates
- Handles network errors (shows broken Wi-Fi icon and semi-diagnostic error messages)

### Advanced Features
- Options to adjust brightness, data refresh interval, screen rotation
- Ability to self-restart the script, restart networking (in case if crashes), restart and shutdown the host Pi
- Test mode with random data for features display testing (toggle-able via hidden menu)
- Dual-language support (Romanian and English)

### Visual Feedback
- Color-coded values (red/green/blue for configurable thresholds)
- Icons for solar, grid, house, battery, fans, thermometer
- Over-temperature, over-voltage alert indicators
- Inverter addon fan status indicator
- Inverter off-grid alert (red background)
- Network information display on restart
- Loading spinner during actions (restart, shutdown)

---

## How to Use

> [!WARNING]
> **Note**: This code is **seriously** hardcoded for my specific setup, sensors configuration and IDs, devices and requirements. Will require extensive configuration, adjusting and testing to fit your usage case. This script should only be taken as an example on how things can be done and a starting point, not a ready-to-use piece of software. 

### Hardware Setup
1. Enable SPI and I2C on Raspberry Pi:
   ```bash
   sudo raspi-config
   ```
2. Install dependencies:
   ```bash
   sudo apt install python3-pip python3-pigpio fonts-dejavu-core fonts-dejavu-extra fonts-symbola
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


### Sensors
The sensor IDs are defined in the `dash_setup.py` file. The energy and solar screens (5 and 1) require all sensors to exist to have the required amount of data for display. The other screens (2, 3 and 4) will auto-adjust to fit the list of sensors defined.

Additional ID-specific parameters are set in the same in `dash_setup.py` with the random value initialization for test mode hardcoded in `dash_functions.py` (for now). Temperature sensors accept a _warning_ value that will color them red. The lower limit warning value is hardcoded to 10°C. Other sensors also accept threshold or default values that trigger their alternate color. 

All device labels, names, menu items and messages displayed on the screen now have dual-language support and are loaded from `dash_translation.py`.


### Test the Dashboard
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


### Changelog

See [`dash_setup.py`](https://github.com/thezedt/pidash/blob/main/dash_setup.py#L24)

---

![Dashboard Temps Screen](/assets/dashboard-2.jpg)

![Dashboard Energy Screen](/assets/dashboard-3.jpg)

---