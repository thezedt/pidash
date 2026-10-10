#!/usr/bin/env python3
"""Fonts, the Home Assistant client, and dashboard/error rendering."""

### needs packages: 
###     fonts-dejavu-core 
###     pigpio python3-pigpio
###
### systemctl enable --now pigpiod

from PIL import Image, ImageDraw, ImageFont
import requests

import dash_config
import dash_setup
import dash_helpers

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
except OSError:
    FONT_TINY = ImageFont.load_default()
    FONT_SMALL = FONT_TINY
    FONT_VALUE = FONT_SMALL


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


def draw_dashboard(lcd, values):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    #                     #
    #     Top: SOLAR      #
    #                     #
    solar_power = values["solar"]

    # handle value length
    if len(dash_helpers.watts(values["solar"])) > 3:
        offset = 4
    else:
        offset = 0

    solar_color = dash_helpers.active_color(
        solar_power, 100, dash_setup.SOLAR_ACTIVE_COLOR, dash_setup.SOLAR_IDLE_COLOR
    )

    dash_helpers.draw_solar_icon(draw, 36 - offset * 2, 3, solar_color)

    dash_helpers.text_center(
        draw,
        (72 + offset, 5),  # LEFT,TOP
        dash_helpers.watts(values["solar"]),
        solar_color,
        FONT_VALUE,
    )

    #                     #
    #  Left-middle: GRID  #
    #                     #
    grid_power = values["grid_power"]
    grid_icon_color = dash_setup.WHITE
    grid_value_color = dash_setup.WHITE

    if grid_power is None:
        # invalid data
        grid_text = "--"
        grid_label_color = dash_setup.IDLE_COLOR
        grid_icon_color = dash_setup.IDLE_COLOR
        grid_value_color = dash_setup.IDLE_COLOR

    elif grid_power == 0:
        # Skip arrow on zero grid
        grid_text = dash_helpers.watts_abs(grid_power)
        grid_label_color = dash_setup.IDLE_COLOR
        grid_icon_color = dash_setup.IDLE_COLOR
        grid_value_color = dash_setup.IDLE_COLOR

    elif grid_power > 0:
        # Positive means importing from the grid
        grid_text = dash_helpers.watts_abs(grid_power)
        grid_label_color = dash_setup.RED

        arrow_color = dash_helpers.active_color(
            grid_power, 100, dash_setup.RED, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_horizontal_arrow(draw, 25, 30, "right", arrow_color)

    else:
        # Negative means exporting to the grid
        grid_text = dash_helpers.watts_abs(grid_power)
        grid_label_color = dash_setup.GREEN

        arrow_color = dash_helpers.active_color(
            grid_power, 100, dash_setup.GREEN, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_horizontal_arrow(draw, 25, 30, "left", arrow_color)

    dash_helpers.draw_grid_icon(draw, 5, 23, grid_icon_color)

    grid_value_color = dash_helpers.over_limit_color(
        grid_power, 1000, dash_setup.RED, grid_value_color
    )

    draw.text(
        (5, 43),  # LEFT,TOP
        grid_text,
        fill=grid_value_color,
        font=FONT_VALUE,
    )

    #                       #
    #  Right-middle: HOUSE  #
    #                       #
    dash_helpers.draw_house_icon(draw, 90, 23, dash_setup.WHITE)

    house_power = values["house"]
    house_value_color = dash_helpers.over_limit_color(
        house_power, 1000, dash_setup.RED, dash_setup.WHITE
    )

    draw.text(
        (75, 43),
        dash_helpers.watts(values["house"]),
        fill=house_value_color,
        font=FONT_VALUE,
    )

    #                        #
    # Center-bottom: BATTERY #
    #                        #
    battery_power = values["battery_power"]

    if battery_power is None:
        # Skip arrow on zero color
        battery_text = dash_helpers.watts_abs(battery_power)
        battery_label_color = dash_setup.IDLE_COLOR

    elif battery_power < 0:
        # Negative means charging
        battery_text = dash_helpers.watts_abs(battery_power)
        battery_label_color = dash_setup.WHITE

        arrow_color = dash_helpers.active_color(
            battery_power, 100, dash_setup.GREEN, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_vertical_arrow(draw, 29, 67, "down", arrow_color)

    elif battery_power > 0:
        # Positive means discharging
        battery_text = dash_helpers.watts_abs(battery_power)
        battery_label_color = dash_setup.WHITE

        arrow_color = dash_helpers.active_color(
            battery_power, 100, dash_setup.RED, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_vertical_arrow(draw, 29, 67, "up", arrow_color)

    else:
        battery_text = "0 W"
        battery_label_color = dash_setup.WHITE

    battery_value_color = dash_helpers.over_limit_color(
        battery_power, 1000, dash_setup.RED, dash_setup.WHITE
    )

    level = values["battery_level"]
    battery_limit = values["battery_limit"]

    if level < battery_limit:
        battery_icon_color = dash_setup.IDLE_COLOR
    else:
        battery_icon_color = dash_setup.WHITE

    dash_helpers.draw_battery_icon(draw, 42, 67, battery_icon_color)

    draw.text(
        (64, 61),
        battery_text,
        fill=battery_value_color,
        font=FONT_SMALL,
    )

    if level is not None and level >= 0:
        battery_level_color = dash_setup.WHITE
    else:
        battery_level_color = dash_setup.RED

    if level < battery_limit:
        battery_level_color = dash_setup.IDLE_COLOR

    # Battery percentage
    if level is not None:
        draw.text(
            (64, 72),
            f"{level:.0f}%",
            fill=battery_level_color,
            font=FONT_VALUE,
        )

    # Battery runtime
    runtime_text = dash_helpers.format_runtime(values["battery_runtime"])
    draw.text(
        (50, 88),
        runtime_text,
        fill=dash_setup.IDLE_COLOR,
        font=FONT_TINY,
    )

    # END
    lcd.display(image)
