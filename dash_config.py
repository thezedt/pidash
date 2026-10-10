#!/usr/bin/env python3
"""Configuration for the Home Assistant dashboard.

Keep this file out of version control if you hardcode a real HA_TOKEN here -
prefer setting HA_URL / HA_TOKEN as environment variables instead.
"""

import os

# -----------------------------
# Home Assistant connection
# -----------------------------
HA_URL = os.getenv("HA_URL", "http://REDACTED:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "REDACTED")
# HA_TOKEN = os.environ["HA_TOKEN"]

# -----------------------------
# Sensors
# -----------------------------
SENSORS = {
    "solar": "sensor.inverter_input_power",
    "house": "sensor.shelly_pro_em50_energy_meter_home_true_power",
    "battery_power": "sensor.battery_1_charge_discharge_power_inverted",  # negative for charging, positive for discharging
    "battery_level": "sensor.battery_1_state_of_capacity",
    "battery_limit": "number.batteries_backup_power_soc",
    "grid_power": "sensor.power_meter_active_power_inverted",  # negative for export, positive for import
    "battery_runtime": "sensor.battery_time_remaining",
}

UPDATE_SECONDS = 5

# -----------------------------
# Hardware
# -----------------------------

# Backlight
BACKLIGHT_PIN = 24

# Waveshare 1.44-inch LCD HAT, model 13891
LCD_WIDTH = 128
LCD_HEIGHT = 128
LCD_SPI_PORT = 0
LCD_SPI_DEVICE = 0
LCD_GPIO_DC = 25
LCD_GPIO_RST = 27
LCD_ROTATE = 0
LCD_H_OFFSET = 2
LCD_V_OFFSET = 0
LCD_BGR = True
