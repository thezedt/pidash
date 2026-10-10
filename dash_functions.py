#!/usr/bin/env python3
"""Fonts, the Home Assistant client, and dashboard/error rendering."""

### needs packages: 
###     fonts-dejavu-core 
###     fonts-dejavu-extra
###     pigpio python3-pigpio
###
### systemctl enable --now pigpiod

from PIL import Image, ImageDraw, ImageFont
import requests
import os
import threading
import time
import textwrap
import random # for debug tests
from datetime import datetime
import ipaddress
import socket
import subprocess

import dash_config
import dash_setup
import dash_helpers
import dash_screens

# -----------------------------
# Fonts
# -----------------------------
try:
    FONT_TINY = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
    )
    FONT_VALUE = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
    )
    FONT_CONDENSED = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", 11
    )
except OSError:
    FONT_TINY = ImageFont.load_default()
    FONT_SMALL = FONT_TINY
    FONT_VALUE = FONT_SMALL
    FONT_CONDENSED = FONT_TINY

# -----------------------------
# Home Assistant client
# -----------------------------

_ha_reachable = True
_ha_state_lock = threading.Lock()

def is_ha_reachable():
    with _ha_state_lock:
        return _ha_reachable


def set_ha_reachable(value):
    global _ha_reachable

    with _ha_state_lock:
        _ha_reachable = value


def get_state(entity_id):
    url = f"{dash_config.HA_URL.rstrip('/')}/api/states/{entity_id}"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {dash_config.HA_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        set_ha_reachable(True)

        try:
            return float(data["state"])
        except (ValueError, TypeError):
            return None

    except requests.RequestException:
        set_ha_reachable(False)
        raise


def get_state_raw(entity_id):
    """Return the Home Assistant state without converting it to float."""
    url = f"{dash_config.HA_URL.rstrip('/')}/api/states/{entity_id}"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {dash_config.HA_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        set_ha_reachable(True)

        state = data["state"]

        if state in ("unknown", "unavailable"):
            return None

        return state

    except requests.RequestException:
        set_ha_reachable(False)
        raise

def read_all_states():
    """Read all Home Assistant entity states with one API request."""
    url = f"{dash_config.HA_URL.rstrip('/')}/api/states"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {dash_config.HA_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=5,
    )
    response.raise_for_status()

    states = response.json()

    # Convert:
    # [{"entity_id": "...", "state": "..."}, ...]
    # into:
    # {"entity_id": {"state": "...", ...}, ...}
    return {
        item["entity_id"]: item
        for item in states
        if "entity_id" in item
    }


# Sensors whose HA state is not a plain number and must be fetched with
# get_state_raw() instead of get_state() - e.g. binary_sensor.charging
# ("on"/"off"), or spring_time_to_limit which Home Assistant already
# formats as a string like "3h 20m".
RAW_STRING_SENSORS = {"spring_charge_status", "spring_time_to_limit", "inverter_grid_status"}
def read_values():
    values = {}

    try:
        all_states = read_all_states()
        set_ha_reachable(True)

    except requests.RequestException as error:
        print(f"Home Assistant request failed: {error}")
        set_ha_reachable(False)

        # Preserve the expected keys so the rendering code can continue.
        for name in dash_setup.SENSORS:
            values[name] = None

        values["pi_temp"] = get_pi_temperature()
        return values

    for name, entity_id in dash_setup.SENSORS.items():
        entity = all_states.get(entity_id)

        if entity is None:
            values[name] = None
            continue

        raw_state = entity.get("state")

        if raw_state in ("unknown", "unavailable", None):
            values[name] = None
            continue

        if name in RAW_STRING_SENSORS:
            values[name] = raw_state
        else:
            try:
                values[name] = float(raw_state)
            except (ValueError, TypeError):
                values[name] = None

    values["pi_temp"] = get_pi_temperature()

    # TEST MODE overrides
    if dash_setup.TEST_MODE:
        values["solar"] = round(random.uniform(0, 5500), 2) #sensor.inverter_input_power
        values["house"] = round(random.uniform(0, 5500), 2) #sensor.shelly_pro_em50_energy_meter_home_true_power
        values["battery_power"] = round(random.uniform(-1500, 1500), 2) #sensor.battery_1_charge_discharge_power_inverted  # negative for charging, positive for discharging
        values["battery_level"] = random.randint(0, 100)#sensor.battery_1_state_of_capacity
        values["battery_limit"] = random.randint(0, 100)#number.batteries_backup_power_soc
        values["grid_power"] = round(random.uniform(-2500, 2500), 2) #sensor.power_meter_active_power_inverted  # negative for export, positive for import
        values["grid_voltage"] = round(random.uniform(225, 265), 2) #sensor.failsafe_grid_voltage
        values["battery_runtime"] = random.randint(0, 5999) #5999 #sensor.battery_time_remaining # minutes !
        values["inverter_temp"] = round(random.uniform(-10, 55), 2) #sensor.inverter_internal_temperature
        values["battery_bms_temp"] = round(random.uniform(-10, 55), 2) #sensor.battery_1_temperature
        values["battery_avg_temp"] = round(random.uniform(-10, 55), 2) #sensor.battery_1_average_temperature

        values["battery_pack1_avg_temp"] = round(random.uniform(-10, 55), 2) #sensor.battery_1_pack_1_average_temperature
        values["battery_pack2_avg_temp"] = round(random.uniform(-10, 55), 2) #sensor.battery_1_pack_2_average_temperature
        values["outside_temp"] = round(random.uniform(-25, 65), 2) #sensor.ewelink_snzb_02p_temperature
        values["outside_hum"] = round(random.uniform(0, 100), 2) #sensor.ewelink_snzb_02p_humidity
        values["outside2_temp"] = round(random.uniform(-10, 55), 2) #sensor.sonoff_snzb_02p_3_temperature
        values["outside2_hum"] = round(random.uniform(0, 95), 2) #sensor.sonoff_snzb_02p_3_humidity
        values["hallway_temp"] = round(random.uniform(-10, 45), 2) #sensor.hallway_temp_hum_3_temperature
        values["hallway_hum"] = round(random.uniform(0, 90), 2) #sensor.hallway_temp_hum_3_humidity
        values["pantry_temp"] = round(random.uniform(-10, 55), 2) #sensor.sonoff_snzb_02p_4_temperature
        values["pantry_hum"] = round(random.uniform(0, 95), 2) #sensor.sonoff_snzb_02p_4_humidity
        values["attic_temp"] = round(random.uniform(-15, 75), 2) #sensor.ts0201_h_t_z_1_temperature
        values["bicaz_temp"] = round(random.uniform(-10, 55), 2) #sensor.bicaz_temp_hum_iv_temperature

        values["inverter_derating"] = random.randint(100, 5500)#number.inverter_power_derating
        values["inverter_grid_status"] = random.choice(["On-Grid", "Off-Grid", "On-Grid"]) #sensor.inverter_off_grid_status
        values["battery_backup_level"] = random.randint(10, 100)#number.batteries_backup_power_soc
        values["battery_charge_power"] = random.randint(500, 5000)#number.batteries_maximum_charging_power
        values["battery_discharge_power"] = random.randint(500, 5000)#number.batteries_maximum_discharging_power

        values["spring_battery_level"] = round(random.uniform(0, 100), 2) #sensor.battery
        values["spring_charge_status"] = random.choice(["on", "off"]) #binary_sensor.charging
        values["spring_charge_power"] = random.randint(0, 9999) #sensor.feyree_ev_charger_power_in_watts
        values["spring_charge_current"] = round(random.uniform(0, 32), 2) #number.feyree_ev_charger_set_charge_current
        values["spring_time_to_limit"] = "1h 23m" #sensor.spring_time_remaining_2 # string !
        values["spring_kwh_to_limit"] = round(random.uniform(0, 26), 2) #sensor.spring_charge_capacity_remaining
        values["spring_temp"] = round(random.uniform(-10, 65), 2) #sensor.shelly_blu_h_t_ble_temperature
    # end TEST MODE

    return values


# -----------------------------
# Background Home Assistant fetch
# -----------------------------
#
# read_values() makes one blocking HTTP request per sensor. Calling it
# directly from the main loop freezes button handling/rendering for as
# long as that takes. Instead, the main loop calls request_values_refresh()
# (non-blocking) and reads get_latest_values() every frame; the actual
# fetch runs on a background thread.

_values_lock = threading.Lock()
_latest_values = {}
_fetching = False
_values_version = 0


def set_latest_values(new_values):
    """Seed/replace the latest known values. Used for the initial
    synchronous read at startup, and by the background fetch worker."""
    global _values_version
    with _values_lock:
        _latest_values.clear()
        _latest_values.update(new_values)
        _values_version += 1


def get_values_version():
    """Monotonically increasing counter, bumped each time new values are
    set. Lets the main loop detect 'did the data change?' cheaply, without
    comparing dicts."""
    with _values_lock:
        return _values_version


def get_latest_values():
    with _values_lock:
        return dict(_latest_values)


def is_fetching():
    return _fetching


def _fetch_worker():
    global _fetching
    set_latest_values(read_values())
    _fetching = False


def request_values_refresh():
    """Kick off a background Home Assistant fetch if one isn't already
    running."""
    global _fetching

    if _fetching:
        return

    _fetching = True
    threading.Thread(target=_fetch_worker, daemon=True).start()


# -----------------------------
# Display
# -----------------------------


def draw_error_(lcd, error):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    draw.text((5, 5), "PI Dash", fill="white", font=FONT_SMALL)
    draw.text((5, 22), "\u26A0 Error", fill="red", font=FONT_SMALL)

    message = str(error).replace("\n", " ")
    draw.text((5, 40), message[:24], fill="white", font=FONT_TINY)
    draw.text((5, 55), message[21:42], fill="white", font=FONT_TINY)
    draw.text((5, 70), message[42:64], fill="white", font=FONT_TINY)
    draw.text((5, 85), message[64:86], fill="white", font=FONT_TINY)

    lcd.display(image)

def draw_error(lcd, error):
    width, height = 128, 128
    line_height = 15
    text_x = 5
    text_y = 25
    chars_per_line = 24

    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    draw.text( (5, 5), "PI Dash", fill="white", font=FONT_SMALL )
    draw.text( (50, 5), "Error \u26A0", fill="red", font=FONT_SMALL )

    message = str(error).replace("\n", " ").strip()

    lines = textwrap.wrap(
        message,
        width=chars_per_line,
        break_long_words=True,
        break_on_hyphens=False
    )

    # Calculate the number of lines that fit below the header.
    max_lines = (height - text_y) // line_height

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # Indicate that the message continues.
        lines[-1] = lines[-1][:chars_per_line - 3] + "..."

    for index, line in enumerate(lines):
        y = text_y + index * line_height
        draw.text( (text_x, y), line, fill="white", font=FONT_TINY )

    lcd.display(image)


def render(lcd, state, values, layout=dash_setup.SCREEN_LAYOUT):
    if not is_ha_reachable():
        draw_homeassistant_error(lcd)
        return

    if is_fetching():
        background = "black"
    elif values.get("inverter_grid_status") == "Off-grid":
        background = dash_setup.GRID_ALERT_BG_COLOR
    else:
        background = "black"

    image = Image.new("RGB", (128, 128), background)
    draw = ImageDraw.Draw(image)

    if state.mode == "confirm":
        dash_helpers.draw_confirmation_screen( draw, state.pending_action_label, FONT_SMALL )
    elif state.mode == "menu":
        MENU_ITEMS[5] = hidden_menu_label()
        dash_helpers.draw_vertical_menu(draw, MENU_ITEMS, state.menu_selected, FONT_SMALL)
    else:
        dash_screens.draw_screen(
            draw, state.active_screen, values, FONT_TINY, FONT_SMALL, FONT_VALUE, FONT_CONDENSED, layout
        )
        dash_helpers.draw_screen_indicator(
            draw, state.active_screen + 1, dash_screens.SCREEN_COUNT, FONT_TINY
        )
    if is_fetching():
        dash_helpers.draw_wireless_icon(draw, 3, 116, 9, dash_setup.IDLE_COLOR)

    lcd.display(image)


# -----------------------------
# Buttons
# -----------------------------

NAV_BUTTONS = ("up", "down", "left", "right", "middle", "key1", "key2", "key3")

_button_state = {name: False for name in NAV_BUTTONS}
_button_last_press = {name: 0.0 for name in NAV_BUTTONS}


def read_button_events():
    """Poll the joystick and return the list of buttons newly pressed
    since the last call (debounced)."""
    events = []
    now = time.monotonic()

    for name in NAV_BUTTONS:
        pressed = dash_setup.read_button(name)
        was_pressed = _button_state[name]

        if pressed and not was_pressed:
            if now - _button_last_press[name] >= dash_setup.BUTTON_DEBOUNCE_SECONDS:
                events.append(name)
                _button_last_press[name] = now

        _button_state[name] = pressed

    return events

def hidden_menu_label():
    now = datetime.now().strftime("%H:%M")

    try:
        with open("/proc/uptime", "r") as file:
            uptime_seconds = int(float(file.read().split()[0]))
    except (OSError, ValueError, IndexError):
        uptime_seconds = 0

    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    test_suffix = "T" if dash_setup.TEST_MODE else "-"

    return f"--{now}--{days}d,{hours}:{minutes:02d}-{test_suffix}--"

# -----------------------------
# Menu + screen state machine
# -----------------------------
#
# On the info screens:
#   up/left    -> previous screen (wraps)
#   down/right -> next screen (wraps)
#   middle     -> open the menu
#
# On the menu screen:
#   up/down       -> move selection
#   left          -> exit menu (cancel, screen unchanged)
#   right/middle  -> activate the selected item

MENU_ITEMS = ["« Ieşire", "1: Solar", "2: Temperaturi", "3: Parametri", "4: Spring", "", "Repornire Pi", "Oprire Pi"]
MENU_SELECTABLE_INDEXES = [0, 1, 2, 3, 4, 5, 6, 7]

# KEY1/2/3 are separate physical buttons from the joystick. Each jumps
# straight to its mapped screen from anywhere (closing the menu if it's
# open); pressing the same key again while already on that screen toggles
# back to screen 1.
KEY_SCREEN_MAP = {
    "key1": 1,  # Temps
    "key2": 2,  # Params
    "key3": 3,  # Spring
}


class DashboardState:
    """Tracks which screen (or the menu) is shown, and idles back to
    screen 1 after dash_setup.SCREEN_IDLE_TIMEOUT_SECONDS of inactivity."""

    def __init__(self):
        self.mode = "screen"             # "screen" or "menu"
        self.active_screen = 0           # 0-based index into dash_screens
        self.menu_selected = 0           # index into MENU_ITEMS
        self.pending_action = None       # handle confirmation screen
        self.pending_action_label = ""   # single screen for multiple questions
        self.last_activity = time.monotonic()

    def touch(self):
        self.last_activity = time.monotonic()

    def check_idle(self):
        idle_for = time.monotonic() - self.last_activity

        if idle_for >= dash_setup.SCREEN_IDLE_TIMEOUT_SECONDS:
            if self.mode != "screen" or self.active_screen != 0:
                self.mode = "screen"
                self.active_screen = 0
                self.touch()

    def handle_event(self, button):
        self.touch()

        if button in KEY_SCREEN_MAP:
            self._handle_key_shortcut(button)
        elif self.mode == "screen":
            self._handle_screen_event(button)
        elif self.mode == "menu":
            self._handle_menu_event(button)
        elif self.mode == "confirm":
            self._handle_confirmation_event(button)

    def _handle_key_shortcut(self, button):
        target = KEY_SCREEN_MAP[button]

        if self.mode == "screen" and self.active_screen == target:
            self.active_screen = 0
        else:
            self.mode = "screen"
            self.active_screen = target

    def _handle_screen_event(self, button):
        if button in ("up", "left"):
            self.active_screen = (self.active_screen - 1) % dash_screens.SCREEN_COUNT
        elif button in ("down", "right"):
            self.active_screen = (self.active_screen + 1) % dash_screens.SCREEN_COUNT
        elif button == "middle":
            self.mode = "menu"
            self.menu_selected = 0  # "< Exit" is always the default selection

    def _handle_menu_event(self, button):
        if button == "left":
            self.mode = "screen"
        elif button == "up":
            self.menu_selected = _step_menu_selection(self.menu_selected, -1)
        elif button == "down":
            self.menu_selected = _step_menu_selection(self.menu_selected, 1)
        elif button in ("right", "middle"):
            self._confirm_menu_selection()

    def _confirm_menu_selection(self):
        selection = self.menu_selected

        if selection == 0:
            # < Exit
            self.mode = "screen"
        elif 1 <= selection <= 4:
            self.mode = "screen"
            self.active_screen = selection - 1
        elif selection == 5:
            dash_setup.TEST_MODE = not dash_setup.TEST_MODE
            #MENU_ITEMS[5] = hidden_menu_label()
        elif selection == 6:
          self.pending_action = restart_system
          self.pending_action_label = MENU_ITEMS[6]
          self.mode = "confirm"
        elif selection == 7:
          self.pending_action = shutdown_system
          self.pending_action_label = MENU_ITEMS[7]
          self.mode = "confirm"

    def _handle_confirmation_event(self, button):
        if button == "middle":
            action = self.pending_action

            self.pending_action = None
            self.pending_action_label = ""
            self.mode = "screen"

            if action is not None:
                action()

        elif button in ("left", "up", "down"):
            # Cancel confirmation
            self.pending_action = None
            self.pending_action_label = ""
            self.mode = "menu"


def _step_menu_selection(current, direction):
    position = MENU_SELECTABLE_INDEXES.index(current)
    position = (position + direction) % len(MENU_SELECTABLE_INDEXES)
    return MENU_SELECTABLE_INDEXES[position]

def restart_system():
    os.system("sudo reboot")
    #return false

def shutdown_system():
    os.system("sudo shutdown now")
    #return false

def get_pi_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = int(file.read().strip()) / 1000
        #return f"{temperature:.1f} \u00b0C"
        return temperature
    except Exception:
        return 0.00
		
##
#   network detection block
#

def get_local_ipv4_addresses():
    """Return globally assigned IPv4 addresses on the Pi."""
    try:
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "scope", "global"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    addresses = []

    for line in result.stdout.splitlines():
        fields = line.split()

        try:
            inet_index = fields.index("inet")
            address = fields[inet_index + 1].split("/", 1)[0]
            addresses.append(ipaddress.ip_address(address))
        except (ValueError, IndexError):
            continue

    return addresses


def get_current_ipv4():
    """Return the first assigned IPv4 address, or None."""
    addresses = get_local_ipv4_addresses()

    if not addresses:
        return None

    return str(addresses[0])


def is_on_required_network():
    """Return True if any local IPv4 address is on expected range."""
    return any(
        address in dash_config.REQUIRED_NETWORK
        for address in get_local_ipv4_addresses()
    )

def get_current_wifi_ssid():
    """Return the current Wi-Fi SSID, or None if unavailable."""
    try:
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )

        ssid = result.stdout.strip()
        return ssid or None

    except (OSError, subprocess.SubprocessError):
        return None



def draw_broken_wifi_icon(draw, x, y, size=64, color="red"):
    """Draw a wide Wi-Fi icon with three arcs and a thin break line."""
    width = int(size * 1.35)
    height = size
    center_x = x + width // 2

    # Three Wi-Fi arcs: outer, middle, and inner.
    arc_specs = (
        (0, 5),
        (14, 5),
        (28, 5),
    )

    for inset, arc_width in arc_specs:
        draw.arc(
            (
                x + inset,
                y + inset,
                x + width - inset,
                y + height - inset,
            ),
            start=225,
            end=315,
            fill=color,
            width=arc_width,
        )

    # Center dot.
    dot_radius = 5
    dot_y = y + height - 7

    draw.ellipse(
        (
            center_x - dot_radius,
            dot_y - dot_radius,
            center_x + dot_radius,
            dot_y + dot_radius,
        ),
        fill=color,
    )

    # Thin diagonal break line.
    draw.line(
        (
            x + 5,
            y + 5,
            x + width - 5,
            y + height - 5,
        ),
        fill=color,
        width=3,
    )


def draw_connection_error(lcd, title, line_one, line_two):
    """Display a connection error using the large broken Wi-Fi icon."""
    width = 128
    height = 128

    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    icon_width = 86
    icon_height = 64
    icon_x = (128 - icon_width) // 2
    icon_y = 4

    draw_broken_wifi_icon(
        draw,
        icon_x,
        icon_y,
        size=icon_height,
        color="red",
    )

    draw.text(
        (width // 2, 76),
        title,
        fill="red",
        font=FONT_VALUE,
        anchor="mm",
    )

    draw.text(
        (width // 2, 96),
        line_one,
        fill="white",
        font=FONT_TINY,
        anchor="mm",
    )

    # Truncate unusually long SSIDs so they do not run off the display.
    if len(line_two) > 22:
        line_two = line_two[:19] + "..."

    draw.text(
        (width // 2, 113),
        line_two,
        fill="white",
        font=FONT_TINY,
        anchor="mm",
    )

    lcd.display(image)

def draw_network_error(lcd):
    current_ip = get_current_ipv4()
    current_ssid = get_current_wifi_ssid()

    draw_connection_error(
        lcd,
        "Eroare Reţea",
        f"Adresă IP: {current_ip or 'neconectat'}",
        f"SSID: {current_ssid or 'neconectat'}",
    )


def draw_homeassistant_error(lcd):
    draw_connection_error(
        lcd,
        "Eroare",
        "Home Assistant",
		"imposibil de conectat"
    )


# end network check block


# FIN