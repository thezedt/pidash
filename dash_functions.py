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
import time

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


def get_state(entity_id):

    url = f"{dash_config.HA_URL.rstrip('/')}/api/states/{entity_id}"

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

    try:
        return float(data["state"])
    except (ValueError, TypeError):
        return None


def read_values():
    values = {}

    for name, entity_id in dash_setup.SENSORS.items():
        try:
            values[name] = get_state(entity_id)
        except requests.RequestException:
            values[name] = None

    return values


# -----------------------------
# Display
# -----------------------------


def draw_error(lcd, error):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    draw.text((5, 5), "PI Dash", fill="white", font=FONT_SMALL)
    draw.text((5, 22), "Connection error", fill="red", font=FONT_SMALL)

    message = str(error).replace("\n", " ")
    draw.text((5, 40), message[:21], fill="white", font=FONT_TINY)
    draw.text((5, 55), message[21:42], fill="white", font=FONT_TINY)
    draw.text((5, 70), message[42:64], fill="white", font=FONT_TINY)
    draw.text((5, 85), message[64:86], fill="white", font=FONT_TINY)

    lcd.display(image)


def render(lcd, state, values):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    if state.mode == "menu":
        dash_helpers.draw_vertical_menu(draw, MENU_ITEMS, state.menu_selected, FONT_SMALL)
    else:
        dash_screens.draw_screen(
            draw, state.active_screen, values, FONT_TINY, FONT_SMALL, FONT_VALUE, FONT_CONDENSED
        )
        dash_helpers.draw_screen_indicator(
            draw, state.active_screen + 1, dash_screens.SCREEN_COUNT, FONT_TINY
        )

    lcd.display(image)


# -----------------------------
# Buttons
# -----------------------------

NAV_BUTTONS = ("up", "down", "left", "right", "middle")

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
MENU_SELECTABLE_INDEXES = [0, 1, 2, 3, 4, 6, 7]


class DashboardState:
    """Tracks which screen (or the menu) is shown, and idles back to
    screen 1 after dash_setup.SCREEN_IDLE_TIMEOUT_SECONDS of inactivity."""

    def __init__(self):
        self.mode = "screen"    # "screen" or "menu"
        self.active_screen = 0  # 0-based index into dash_screens
        self.menu_selected = 0  # index into MENU_ITEMS
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

        if self.mode == "screen":
            self._handle_screen_event(button)
        else:
            self._handle_menu_event(button)

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
        elif selection == 6:
            restart_system()
        elif selection == 7:
            shutdown_system()


def _step_menu_selection(current, direction):
    position = MENU_SELECTABLE_INDEXES.index(current)
    position = (position + direction) % len(MENU_SELECTABLE_INDEXES)
    return MENU_SELECTABLE_INDEXES[position]


def restart_system():
    os.system("sudo reboot")


def shutdown_system():
    os.system("sudo shutdown now")
