#!/usr/bin/env python3
"""Fonts, the Home Assistant client, and dashboard/error rendering."""

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
RAW_STRING_SENSORS = {"spring_charge_status", "spring_time_to_limit", "inverter_grid_status", "inverter_fans_1", "inverter_fans_2"}
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
        values["inverter_fans_1"] = random.choice(["on", "off"]) #switch.sonoff_10021e6428_1
        values["inverter_fans_2"] = random.choice(["on", "off"]) #switch.sonoff_10021e6428_2

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

        values["energy_solar_kwh"] = random.randint(0, 100)
        values["energy_grid_import_kwh"] = random.randint(0, 100)
        values["energy_grid_export_kwh"] = random.randint(0, 100)
        values["energy_house_kwh"] = random.randint(0, 100)
        values["energy_battery_discharge_kwh"] = random.randint(0, 100)
        values["energy_battery_charge_kwh"] = random.randint(0, 100)
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

_current_lcd = None
_current_rotation = dash_setup.SCREEN_ROTATION
# Cached backlight PWM handle (set once from dashboard.main()) so brightness
# changes made from the Advanced submenu take effect immediately, instead
# of waiting for the next periodic sensor-poll cycle.
_backlight_pwm = None

def get_current_rotation():
    return _current_rotation

def set_current_rotation(value):
    global _current_rotation
    _current_rotation = value

def get_current_lcd():
    return _current_lcd

def set_backlight_pwm(pwm):
    global _backlight_pwm
    _backlight_pwm = pwm


def compute_brightness():
    # lower brightness between 23:30 and 07:30
    now = time.localtime()
    minutes = now.tm_hour * 60 + now.tm_min

    # Quiet period: 23:30 through 07:30
    if minutes >= 22 * 60 + 30 or minutes < 7 * 60 + 30:
        return dash_setup.NIGHT_BRIGHTNESS
    return dash_setup.DAY_BRIGHTNESS


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

    # Apply rotation
    if get_current_rotation() == 180:
        image = image.rotate(180, expand=False)
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

    # Apply rotation
    if get_current_rotation() == 180:
        image = image.rotate(180, expand=False)
    lcd.display(image)


def render(lcd, state, values, layout=dash_setup.SCREEN_LAYOUT):
    global _current_lcd
    _current_lcd = lcd

    if not is_ha_reachable() and state.mode == "screen":
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

#    if state.mode == "confirm":
#        dash_helpers.draw_confirmation_screen( draw, state.pending_action_label, FONT_SMALL )
#    elif state.mode == "menu":
#        MENU_ITEMS[5] = hidden_menu_label()
#        dash_helpers.draw_vertical_menu(draw, MENU_ITEMS, state.menu_selected, FONT_SMALL)
#    else:
    if state.mode == "confirm":
        dash_helpers.draw_confirmation_screen( draw, state.pending_action_label, FONT_SMALL )
    elif state.mode == "menu":
        dash_helpers.draw_vertical_menu(draw, MENU_ITEMS, state.menu_selected, FONT_SMALL)
    elif state.mode == "submenu":
        poll_network_restart_status()
#        dash_helpers.draw_vertical_menu(draw, build_submenu_items(), state.menu_selected, FONT_SMALL)
        submenu_items = build_submenu_items()
        dash_helpers.draw_vertical_menu_scrollable(draw, submenu_items, state.menu_selected, state.submenu_scroll, FONT_SMALL)
    else:
        dash_screens.draw_screen(
            draw, state.active_screen, values, FONT_TINY, FONT_SMALL, FONT_VALUE, FONT_CONDENSED, layout
        )
        dash_helpers.draw_screen_indicator(
            draw, state.active_screen + 1, dash_screens.SCREEN_COUNT, FONT_TINY
        )
    if is_fetching():
        dash_helpers.draw_wireless_icon(draw, 3, 116, 9, dash_setup.IDLE_COLOR)

    # Apply rotation
    if state.screen_rotation == 180:
        image = image.rotate(180, expand=False)
    lcd.display(image)


# -----------------------------
# Buttons
# -----------------------------

NAV_BUTTONS = ("up", "down", "left", "right", "middle", "key1", "key2", "key3")

_button_state = {name: False for name in NAV_BUTTONS}
_button_last_press = {name: 0.0 for name in NAV_BUTTONS}

_combo_active = False

def read_button_events():
    """Poll the joystick and return the list of buttons newly pressed
    since the last call (debounced). Also emits a synthetic "menu_combo"
    event if key1 and key3 are held down at the same time, as an
    alternative to the middle button for opening the menu."""
    global _combo_active

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

    if _button_state["key1"] and _button_state["key3"]:
        if not _combo_active:
            events.append("menu_combo")
            _combo_active = True
    else:
        _combo_active = False

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

#MENU_ITEMS = ["« Ieşire", "1: Solar", "2: Temperaturi", "3: Parametri", "4: Spring", "", "Repornire Pi", "Oprire Pi"]
#MENU_SELECTABLE_INDEXES = [0, 1, 2, 3, 4, 5, 6, 7]
MENU_ITEMS = ["« Ieşire", "1: Solar", "2: Temperaturi", "3: Parametri", "4: Spring", "5: Energie", "", "Avansat »"]
MENU_SELECTABLE_INDEXES = [0, 1, 2, 3, 4, 5, 7]

# Advanced submenu, opened from main menu item 7 ("Advanced >>").
# Item 4 is left blank for future use.
#
# On items 2 (brightness) and 3 (refresh), left/right adjust the value
# in place instead of moving the selection - see
# DashboardState._handle_submenu_event.
SUBMENU_SELECTABLE_INDEXES = [0, 2, 3, 4, 5, 6, 8, 9, 11]


def build_submenu_items():
    """Build the Advanced submenu labels fresh each render, since three of
    them show live state (network-restart status, brightness, refresh
    interval, and the test-mode clock/uptime label)."""
    rotation_label = "180°" if get_current_rotation() == 180 else "0°"
    return [
        "« Înapoi",
        "",  # Separator
        dash_helpers.scrolling_text(get_network_restart_label("Repornire reţea")),
        f"Luminozitate: {dash_setup.DAY_BRIGHTNESS}%",
        f"Interval: {dash_setup.UPDATE_SECONDS}s",
        f"Rotație ecran: {rotation_label}",
        "Repornire PiDash",
        "",  # Separator
        "* Repornire Pi",
        "* Oprire Pi",
        "",  # Separator
        hidden_menu_label(),
    ]

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
        self.mode = "screen"             # "screen", "menu", "submenu", or "confirm"
        self.active_screen = 0           # 0-based index into dash_screens
        self.screen_rotation = dash_setup.SCREEN_ROTATION
        self.submenu_scroll = 0          # Scroll offset for submenu
        self.menu_selected = 0           # index into MENU_ITEMS or the submenu items
        self.pending_action = None       # handle confirmation screen
        self.pending_action_label = ""   # single screen for multiple questions
        self.confirm_return_mode = "menu"  # where "confirm" goes back to on cancel
        self.last_activity = time.monotonic()

    def touch(self):
        self.last_activity = time.monotonic()

    def check_idle(self):
        idle_for = time.monotonic() - self.last_activity

        if idle_for >= dash_setup.SCREEN_IDLE_TIMEOUT_SECONDS:
            if self.mode != "screen" or self.active_screen != 0:
                if self.mode == "submenu":
                    clear_network_restart_label()
                self.mode = "screen"
                self.active_screen = 0
                self.touch()

    def handle_event(self, button):
        self.touch()

        # Swap joystick directions when screen is rotated 180 degrees
        if self.screen_rotation == 180:
            if button == "up":
                button = "down"
            elif button == "down":
                button = "up"
            elif button == "left":
                button = "right"
            elif button == "right":
                button = "left"

        if button == "menu_combo":
            if self.mode == "screen":
                self.mode = "menu"
                self.menu_selected = 0
        elif button in KEY_SCREEN_MAP:
            self._handle_key_shortcut(button)
        elif self.mode == "screen":
            self._handle_screen_event(button)
        elif self.mode == "menu":
            self._handle_menu_event(button)
        elif self.mode == "submenu":
            self._handle_submenu_event(button)
        elif self.mode == "confirm":
            self._handle_confirmation_event(button)

    def _handle_key_shortcut(self, button):
        target = KEY_SCREEN_MAP[button]

        # When rotated 180, swap KEY1 and KEY3 targets
        if self.screen_rotation == 180:
            if button == "key1":
                target = KEY_SCREEN_MAP["key3"]
            elif button == "key3":
                target = KEY_SCREEN_MAP["key1"]

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
        elif 1 <= selection <= 5:
            self.mode = "screen"
            self.active_screen = selection - 1
        elif selection == 7:
            # "Advanced >>"
            self.mode = "submenu"
            self.menu_selected = 0

    def _handle_submenu_event(self, button):
        # Items 2 (brightness) and 3 (refresh) use left/right to adjust
        # their value in place instead of the usual back/confirm meaning.
        submenu_items = build_submenu_items()
        visible_items = 8  # Number of items that fit on screen
        max_scroll = max(0, len(submenu_items) - visible_items)

        if self.menu_selected == 3 and button in ("left", "right"):
            self._adjust_brightness(button)
        elif self.menu_selected == 4 and button in ("left", "right"):
            self._adjust_refresh(button)
        elif self.menu_selected == 5 and button in ("left", "right"):
            self._toggle_rotation()
        elif button == "left":
            self._leave_submenu()
        elif button == "up":
            prev_selected = self.menu_selected
            self.menu_selected = _step_submenu_selection(self.menu_selected, -1)
            # Handle wrap-around from 0 to last
            if prev_selected == 0 and self.menu_selected == SUBMENU_SELECTABLE_INDEXES[-1]:
                self.submenu_scroll = max_scroll
            elif self.menu_selected < self.submenu_scroll:
                self.submenu_scroll = self.menu_selected
        elif button == "down":
            prev_selected = self.menu_selected
            self.menu_selected = _step_submenu_selection(self.menu_selected, 1)
            # Handle wrap-around from last to 0
            if prev_selected == SUBMENU_SELECTABLE_INDEXES[-1] and self.menu_selected == 0:
                self.submenu_scroll = 0
            elif self.menu_selected >= self.submenu_scroll + visible_items:
                self.submenu_scroll = min(self.menu_selected - visible_items + 1, max_scroll)
        elif button in ("right", "middle"):
            self._confirm_submenu_selection()

    def _toggle_rotation(self):
        self.screen_rotation = 180 if self.screen_rotation == 0 else 0
        set_current_rotation(self.screen_rotation)

    def _adjust_brightness(self, button):
        step = 10 if button == "right" else -10
        new_value = max(10, min(100, dash_setup.DAY_BRIGHTNESS + step))
        dash_setup.DAY_BRIGHTNESS = new_value
        dash_setup.NIGHT_BRIGHTNESS = new_value

        if _backlight_pwm is not None:
            _backlight_pwm.set_PWM_dutycycle(dash_setup.BACKLIGHT_PIN, compute_brightness())

    def _adjust_refresh(self, button):
        step = 1 if button == "right" else -1
        dash_setup.UPDATE_SECONDS = max(3, min(20, dash_setup.UPDATE_SECONDS + step))

    def _leave_submenu(self):
        clear_network_restart_label()
        self.mode = "menu"
        self.menu_selected = 7  # land back on "Advanced >>"

    def _confirm_submenu_selection(self):
        selection = self.menu_selected

        if selection == 0:
            # « Înapoi
            self._leave_submenu()
        elif selection == 2:
            restart_network()
        elif selection == 5:
            self._toggle_rotation()
        elif selection == 6:
            restart_script()
        elif selection == 8:
          self.pending_action = restart_system
          self.pending_action_label = "Repornire Pi"
          self.confirm_return_mode = "submenu"
          self.mode = "confirm"
        elif selection == 9:
          self.pending_action = shutdown_system
          self.pending_action_label = "Oprire Pi"
          self.confirm_return_mode = "submenu"
          self.mode = "confirm"
        elif selection == 11:
            dash_setup.TEST_MODE = not dash_setup.TEST_MODE
            #MENU_ITEMS[5] = hidden_menu_label()

    def _handle_confirmation_event(self, button):
        if button in ("middle", "right"):
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
            self.mode = self.confirm_return_mode


def _step_menu_selection(current, direction):
    position = MENU_SELECTABLE_INDEXES.index(current)
    position = (position + direction) % len(MENU_SELECTABLE_INDEXES)
    return MENU_SELECTABLE_INDEXES[position]

def _step_submenu_selection(current, direction):
    position = SUBMENU_SELECTABLE_INDEXES.index(current)
    position = (position + direction) % len(SUBMENU_SELECTABLE_INDEXES)
    return SUBMENU_SELECTABLE_INDEXES[position]

def restart_system():
    if _current_lcd is not None:
        image = Image.new("RGB", (128, 128), "black")
        draw = ImageDraw.Draw(image)
        dash_helpers.draw_hourglass_icon(draw, 64, 64, dash_setup.WHITE)
        _current_lcd.display(image)

    os.system("sudo reboot")
    #return false

def shutdown_system():
    if _current_lcd is not None:
        image = Image.new("RGB", (128, 128), "black")
        draw = ImageDraw.Draw(image)
        dash_helpers.draw_hourglass_icon(draw, 64, 64, dash_setup.WHITE)
        _current_lcd.display(image)

    os.system("sudo shutdown now")
    #return false

def restart_script():
    if _current_lcd is not None:
        image = Image.new("RGB", (128, 128), "black")
        draw = ImageDraw.Draw(image)
        dash_helpers.draw_hourglass_icon(draw, 64, 64, dash_setup.WHITE)
        _current_lcd.display(image)

    os.system("sudo systemctl restart dashboard.service")
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

##
#   network restart (Advanced submenu item 1)
#
# restart_network() is intentionally left as a no-op for now - wire up the
# actual system call once we've settled on NetworkManager vs
# dhcpcd/wpa_supplicant for this device, e.g.:
#   os.system("sudo systemctl restart NetworkManager")
#
# The label shown in the submenu updates itself: "Restarting network..."
# immediately, then flips to "<SSID> / <IP>" once connectivity is back
# (checked every NETWORK_RESTART_CHECK_INTERVAL seconds via
# poll_network_restart_status(), called from render() while the submenu
# is visible). The "connected" label then sticks until another restart is
# triggered, or the submenu is left/times out (see DashboardState).

NETWORK_RESTART_CHECK_INTERVAL = 3  # seconds between reachability re-checks

_network_restart_pending = False
_network_restart_label = None
_network_restart_next_check = 0.0


def restart_network():
    """Kick off a network restart. No-op for now - see note above."""
    global _network_restart_pending, _network_restart_label, _network_restart_next_check


    _network_restart_pending = True
    _network_restart_label = "Repornire reţea..."
    _network_restart_next_check = time.monotonic() + NETWORK_RESTART_CHECK_INTERVAL

    #os.system("sudo ifconfig wlan0 down && sudo ifconfig wlan0 up")
    os.system("sudo systemctl restart NetworkManager")


def poll_network_restart_status():
    """Call periodically (from render(), while the submenu might be
    visible) to update the network-restart label once connectivity
    returns."""
    global _network_restart_pending, _network_restart_next_check, _network_restart_label

    if not _network_restart_pending:
        return

    now = time.monotonic()
    if now < _network_restart_next_check:
        return

    if is_on_required_network():
        ssid = get_current_wifi_ssid()
        ip = get_current_ipv4()
        _network_restart_label = f"{ssid or '?'} / {ip or '?'}"
        _network_restart_pending = False
    else:
        _network_restart_next_check = now + NETWORK_RESTART_CHECK_INTERVAL


def get_network_restart_label(default):
    """Return the current network-restart status label, or `default` if no
    restart has been triggered (or its label has since been cleared)."""
    return _network_restart_label or default


def clear_network_restart_label():
    """Drop the network-restart status label - called when the Advanced
    submenu is left/times out, so a stale "Repornire reţea..." / SSID
    label doesn't linger next time the submenu is opened."""
    global _network_restart_pending, _network_restart_label
    _network_restart_pending = False
    _network_restart_label = None

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

    # Apply rotation
    if get_current_rotation() == 180:
        image = image.rotate(180, expand=False)
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