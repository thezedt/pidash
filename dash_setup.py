#!/usr/bin/env python3
"""Static configuration, color palette, and hardware setup."""

import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
import pigpio

# -----------------------------
# Version info/history
# -----------------------------
VERSION = "v0.2.2"
#
# v0.2.2 - 20260913
# * optimized cpu usage by limiting rendering only on data changes
#
# v0.2.1 - 20260912
# * added handling of network issues and HAS unavailability
# * added spring autonomy km sensor
# * fixed invalid colors for negative grid power
# * fixed display/handling of negative (charging) battery time estimate
#
# v0.2 - 20260909
# * beta state, all screen finalized, most functionality tested
#
# v0.1 - 20260904 
# * first alpha, only home screen with most of the info
#

# -----------------------------
# Sensors
# -----------------------------
SENSORS = {
    # solar - screen 1
    "solar": "sensor.inverter_input_power",
    "house": "sensor.shelly_pro_em50_energy_meter_home_true_power",
    "battery_power": "sensor.battery_1_charge_discharge_power_inverted",  # negative for charging, positive for discharging
    "battery_level": "sensor.battery_1_state_of_capacity",
    "battery_limit": "number.batteries_backup_power_soc",
    "grid_power": "sensor.power_meter_active_power_inverted",  # negative for export, positive for import
    "grid_voltage": "sensor.failsafe_grid_voltage",
    ##"grid_status": "sensor.inverter_off_grid_status",
    "battery_runtime": "sensor.battery_time_remaining",  # minutes !
    "inverter_temp": "sensor.inverter_internal_temperature",
    "battery_bms_temp": "sensor.battery_1_temperature",
    "battery_avg_temp": "sensor.battery_1_average_temperature",
    # details & temps - screen 2
    "battery_pack1_avg_temp": "sensor.battery_1_pack_1_average_temperature",
    "battery_pack2_avg_temp": "sensor.battery_1_pack_2_average_temperature",
    "outside_temp": "sensor.ewelink_snzb_02p_temperature",
    "outside_hum": "sensor.ewelink_snzb_02p_humidity",
    "outside2_temp": "sensor.sonoff_snzb_02p_3_temperature",
    "outside2_hum": "sensor.sonoff_snzb_02p_3_humidity",
    "hallway_temp": "sensor.hallway_temp_hum_3_temperature",
    "hallway_hum": "sensor.hallway_temp_hum_3_humidity",
    "pantry_temp": "sensor.sonoff_snzb_02p_4_temperature",
    "pantry_hum": "sensor.sonoff_snzb_02p_4_humidity",
    "attic_temp": "sensor.ts0201_h_t_z_1_temperature",
    "bicaz_temp": "sensor.bicaz_temp_hum_iv_temperature",
    # extras - screen 3
    "inverter_derating": "number.inverter_power_derating",
    "inverter_grid_status": "sensor.inverter_off_grid_status", # ["On-Grid", "Off-Grid"]
    "battery_backup_level": "number.batteries_backup_power_soc",
    "battery_charge_power": "number.batteries_maximum_charging_power",
    "battery_discharge_power": "number.batteries_maximum_discharging_power",
    # spring - screen 4
    "spring_battery_level": "sensor.battery",
    "spring_charge_status": "binary_sensor.charging", # binary: ["on", "off]
    "spring_charge_power": "sensor.feyree_ev_charger_power_in_watts",
    "spring_charge_current": "number.feyree_ev_charger_set_charge_current",
    "spring_time_to_limit": "sensor.spring_time_remaining_2", # string !
    "spring_kwh_to_limit": "sensor.spring_charge_capacity_remaining",
    "spring_autonomy": "sensor.battery_autonomy",
    "solar_estimate_today_r": "sensor.energy_production_today_remaining",
    "solar_estimate_tomorrow": "sensor.energy_production_tomorrow",
    "spring_temp": "sensor.shelly_blu_h_t_ble_temperature",

}

UPDATE_SECONDS = 10

# How often the button/joystick state is polled.
BUTTON_POLL_SECONDS = 0.05

# Minimum time between accepted presses of the same button (debounce).
BUTTON_DEBOUNCE_SECONDS = 0.15

# Idle time (no button presses) before the dashboard returns to screen 1.
SCREEN_IDLE_TIMEOUT_SECONDS = 60

# Layout for the Params/Spring screens: "stacked" (label above value, safe
# from overlap) or "single_line" (label/value share one line, more
# compact but can overlap if a label is too long for its column).
SCREEN_LAYOUT = "stacked"

# -----------------------------
# Hardware
# -----------------------------

# Backlight
BACKLIGHT_PIN = 24
BACKLIGHT_PWM_FREQUENCY = 1000  # Hz

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

# Waveshare 1.44-inch LCD HAT joystick + buttons
KEY_UP_PIN = 6
KEY_DOWN_PIN = 19
KEY_LEFT_PIN = 5
KEY_RIGHT_PIN = 26
KEY_PRESS_PIN = 13
KEY1_PIN = 21
KEY2_PIN = 20
KEY3_PIN = 16

# Test mode state (triggered by hidden menu item 5)
TEST_MODE = False

BUTTON_PINS = {
    "up": KEY_UP_PIN,
    "down": KEY_DOWN_PIN,
    "left": KEY_LEFT_PIN,
    "right": KEY_RIGHT_PIN,
    "middle": KEY_PRESS_PIN,
    "key1": KEY1_PIN,
    "key2": KEY2_PIN,
    "key3": KEY3_PIN,
}

# background gpio control for pwm smoothness
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("Could not connect to pigpio daemon")

#def setup_backlight_def():
#    GPIO.setmode(GPIO.BCM)
#    GPIO.setwarnings(False)
#    GPIO.setup(BACKLIGHT_PIN, GPIO.OUT, initial=GPIO.HIGH)
#
#def setup_backlight_gpio(brightness=100):
#    GPIO.setmode(GPIO.BCM)
#    GPIO.setwarnings(False)
#    GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
#
#    pwm = GPIO.PWM(BACKLIGHT_PIN, 1000)
#    pwm.start(brightness) # 0–100
#    return pwm

def setup_backlight(brightness=90):
    pi.set_mode(BACKLIGHT_PIN, pigpio.OUTPUT)
    pi.set_PWM_frequency(BACKLIGHT_PIN, BACKLIGHT_PWM_FREQUENCY)
    pi.set_PWM_range(BACKLIGHT_PIN, 100)
    pi.set_PWM_dutycycle(BACKLIGHT_PIN, brightness)
    return pi

def setup_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_button(name):
    """Return True if the given button (see BUTTON_PINS) is currently pressed."""
    return GPIO.input(BUTTON_PINS[name]) == GPIO.LOW

def setup_lcd():

    GPIO.setwarnings(False)
    lcd = st7735(
        spi(
            port=LCD_SPI_PORT,
            device=LCD_SPI_DEVICE,
            gpio_DC=LCD_GPIO_DC,
            gpio_RST=LCD_GPIO_RST,
        ),
        width=LCD_WIDTH,
        height=LCD_HEIGHT,
        rotate=LCD_ROTATE,
        h_offset=LCD_H_OFFSET,
        v_offset=LCD_V_OFFSET,
        bgr=LCD_BGR,
    )
    lcd.cleanup = lambda: None
    return lcd


# -----------------------------
# Color palette
# -----------------------------
BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
GREY = (80, 80, 80)
LIGHT_GREY = (180, 180, 180)
IDLE_COLOR = (120, 120, 120)

SOLAR_IDLE_COLOR = IDLE_COLOR
SOLAR_ACTIVE_COLOR = (255, 210, 0)  # bright yellow

EXPORT_COLOR = (80, 100, 150)
BATTERY_COLOR = (115, 70, 105)
HOUSE_COLOR = (35, 35, 35)

GREEN = (75, 135, 120)
RED = (200, 20, 20)
WARNING_COLOR = (255, 64, 64)
BLUE = (70, 130, 220)

# Screen background while the inverter reports "Off-grid" (see
# grid_status handling in dash_functions.render).
GRID_ALERT_BG_COLOR = (120, 0, 0)

# FIN