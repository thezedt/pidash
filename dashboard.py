#!/usr/bin/env python3

### needs package fonts-dejavu-core ###

import time
import requests
from PIL import Image, ImageDraw, ImageFont
import os
import RPi.GPIO as GPIO

from luma.core.interface.serial import spi
from luma.lcd.device import st7735

# -----------------------------
# Configuration
# -----------------------------

HA_URL = os.getenv("HA_URL", "REDACTED")
HA_TOKEN = os.getenv("HA_TOKEN", "REDACTED")
#HA_TOKEN = os.environ["HA_TOKEN"]

SENSORS = {
    "solar": "sensor.inverter_input_power",
    "house": "sensor.shelly_pro_em50_energy_meter_home_true_power",
    "battery_power": "sensor.battery_1_charge_discharge_power_inverted", # negative for charging, positive for discharging
    "battery_level": "sensor.battery_1_state_of_capacity",
    "battery_limit": "number.batteries_backup_power_soc",
    "grid_power": "sensor.power_meter_active_power_inverted", # negative for export, positive for import
    "battery_runtime": "sensor.battery_time_remaining",
}

UPDATE_SECONDS = 5

# Backlight
BACKLIGHT_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BACKLIGHT_PIN, GPIO.OUT, initial=GPIO.HIGH)

# Waveshare 1.44-inch LCD HAT, model 13891
LCD = st7735(
    spi(
        port=0,
        device=0,
        gpio_DC=25,
        gpio_RST=27,
    ),
    width=128,
    height=128,
    rotate=0,
    h_offset=2,
    v_offset=0,
    bgr=True,
)


# -----------------------------
# Display helpers
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


def draw_error(error):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    draw.text((5, 5), "PI Dash", fill="white", font=FONT_SMALL)
    draw.text((5, 22), "Connection error", fill="red", font=FONT_SMALL)

    message = str(error).replace("\n", " ")
    draw.text((5, 40), message[:21], fill="white", font=FONT_SMALL)
    draw.text((5, 55), message[21:42], fill="white", font=FONT_SMALL)
    draw.text((5, 70), message[42:64], fill="white", font=FONT_SMALL)
    draw.text((5, 85), message[64:86], fill="white", font=FONT_SMALL)

    LCD.display(image)


def get_state(entity_id):

    url = f"{HA_URL.rstrip('/')}/api/states/{entity_id}"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {HA_TOKEN}",
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


def watts(value):
    if value is None:
        return "--"

    absolute = abs(value)

    if absolute >= 1000:
        return f"{value / 1000:.2f} kW"

    return f"{value:.0f} W"


def watts_abs(value):
    if value is None:
        return "--"

    absolute = abs(value)

    if absolute >= 1000:
        return f"{absolute / 1000:.2f} kW"

    return f"{absolute:.0f} W"

def format_runtime(minutes):
    if minutes is None:
        return "   ∞"

    try:
        total_minutes = int(float(minutes))
    except (ValueError, TypeError):
        return "   X"

    if total_minutes < 0:
        total_minutes = 0

    hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    return f"{hours}h {remaining_minutes:02d}m"


def text_center(draw, xy, text, fill, font=FONT_VALUE):
    width = draw.textbbox((0, 0), text, font=font)[2]
    draw.text((xy[0] - width / 2, xy[1]), text, fill=fill, font=font)


# -----------------------------
# Simple monochrome-style icons
# -----------------------------

def draw_solar_icon_(draw, x, y, color):
    # Sun
    draw.ellipse((x + 5, y + 5, x + 13, y + 13), outline=color)
    draw.line((x + 9, y, x + 9, y + 4), fill=color)
    draw.line((x + 9, y + 14, x + 9, y + 18), fill=color)
    draw.line((x, y + 9, x + 4, y + 9), fill=color)
    draw.line((x + 14, y + 9, x + 18, y + 9), fill=color)

def draw_solar_icon(draw, x, y, color):
    # Icon dimensions: approximately 20x20 pixels
    center_x = x + 9
    center_y = y + 9

    ray_width = 1
    ray_radius = ray_width // 2

    def rounded_ray(x1, y1, x2, y2):
        draw.line(
            (x1, y1, x2, y2),
            fill=color,
            width=ray_width,
        )

        # Rounded end caps
        draw.ellipse(
            (
                x1 - ray_radius,
                y1 - ray_radius,
                x1 + ray_radius,
                y1 + ray_radius,
            ),
            fill=color,
        )

        draw.ellipse(
            (
                x2 - ray_radius,
                y2 - ray_radius,
                x2 + ray_radius,
                y2 + ray_radius,
            ),
            fill=color,
        )

    # Filled sun
    draw.ellipse(
        (x + 4, y + 4, x + 14, y + 14),
        fill=color,
    )

    # Cardinal rays
    rounded_ray(center_x, y + 1, center_x, y + 3)       # top
    rounded_ray(center_x, y + 15, center_x, y + 18)     # bottom
    rounded_ray(x + 0, center_y, x + 3, center_y)       # left
    rounded_ray(x + 15, center_y, x + 18, center_y)     # right

    # Diagonal rays
    rounded_ray(x + 2, y + 2, x + 5, y + 5)             # upper-left
    rounded_ray(x + 13, y + 5, x + 16, y + 2)           # upper-right
    rounded_ray(x + 2, y + 16, x + 5, y + 13)           # lower-left
    rounded_ray(x + 13, y + 13, x + 16, y + 16)         # lower-right 

def draw_house_icon(draw, x, y, color):
    draw.polygon(
        [(x, y + 8), (x + 9, y), (x + 18, y + 8)],
        fill=color,
    )
    draw.rectangle((x + 3, y + 8, x + 15, y + 18), fill=color)
    draw.rectangle((x + 8, y + 12, x + 11, y + 18), fill="black")


def draw_battery_icon(draw, x, y, color):
    draw.rectangle((x + 2, y + 2, x + 13, y + 17), outline=color)
    draw.rectangle((x + 5, y, x + 10, y + 2), fill=color)
    draw.rectangle((x + 5, y + 5, x + 10, y + 14), outline=color)


def draw_grid_icon(draw, x, y, color):
    draw.line((x + 9, y, x + 5, y + 18), fill=color, width=2)
    draw.line((x + 9, y, x + 13, y + 18), fill=color, width=2)
    draw.line((x + 3, y + 7, x + 15, y + 7), fill=color, width=2)
    draw.line((x + 5, y + 12, x + 13, y + 12), fill=color, width=2)


def draw_power_flow(draw, x, y, value, color, icon):
    icon(draw, x, y, color)
    draw.text((x + 23, y + 2), watts(value), fill=color, font=FONT_VALUE)

def draw_vertical_arrow(draw, x, y, direction, color):
    """
    Draw a vertical arrow inside approximately 10x18 pixels.

    direction: "up" or "down"
    """
    center_x = x + 4

    if direction == "up":
        # Shaft
        draw.line(
            (center_x, y + 7, center_x, y + 18),
            fill=color,
            width=2,
        )

        # Arrowhead
        draw.polygon(
            [
                (center_x, y),
                (x, y + 7),
                (x + 8, y + 7),
            ],
            fill=color,
        )

    elif direction == "down":
        # Shaft
        draw.line(
            (center_x, y, center_x, y + 11),
            fill=color,
            width=2,
        )

        # Arrowhead
        draw.polygon(
            [
                (x, y + 11),
                (x + 8, y + 11),
                (center_x, y + 18),
            ],
            fill=color,
        )
        
def draw_horizontal_arrow(draw, x, y, direction, color):
    """
    Draw an arrow approximately 18x10 pixels.

    direction: "left" or "right"
    """

    if direction == "right":
        # Horizontal shaft
        draw.line(
            (x, y + 4, x + 11, y + 4),
            fill=color,
            width=3,
        )

        # Arrowhead
        draw.polygon(
            [
                (x + 18, y + 4),
                (x + 11, y),
                (x + 11, y + 8),
            ],
            fill=color,
        )

    elif direction == "left":
        # Horizontal shaft
        draw.line(
            (x + 7, y + 4, x + 18, y + 4),
            fill=color,
            width=3,
        )

        # Arrowhead
        draw.polygon(
            [
                (x, y + 4),
                (x + 7, y),
                (x + 7, y + 8),
            ],
            fill=color,
        )


def draw_dashboard(values):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    black = (30, 30, 30)
    white = (255, 255, 255)
    grey = (80, 80, 80)
    idle_color = (120, 120, 120)
    
    solar_idle_color = idle_color
    solar_active_color = (255, 210, 0)  # bright yellow
    
    export_color = (80, 100, 150)
    battery_color = (115, 70, 105)
    house_color = (35, 35, 35)
    
    green = (75, 135, 120)
    red = (200, 20, 20)

    #                     #
    #     Top: SOLAR      #
    #                     #
    solar_power = values["solar"]

    # handle value length
    if len(watts(values["solar"])) > 3:
        offset = 4
    else:
        offset = 0

    if solar_power is not None and solar_power >= 100:
        solar_color = solar_active_color
    else:
        solar_color = solar_idle_color

    draw_solar_icon(draw, 36-offset*2, 6, solar_color)

    text_center(
        draw,
        (72+offset, 8), # LEFT,TOP
        watts(values["solar"]),
        solar_color,
    )

    #                     #
    #  Left-middle: GRID  #
    #                     #
    grid_power = values["grid_power"]
    grid_icon_color = white
    grid_value_color = white

    if grid_power is None:
        # invalid data
        grid_text = "--"
        grid_label_color = idle_color
        grid_icon_color = idle_color
        grid_value_color = idle_color

    elif grid_power == 0:
        # Skip arrow on zero grid
        grid_text = watts_abs(grid_power)
        grid_label_color = idle_color
        grid_icon_color = idle_color
        grid_value_color = idle_color

    elif grid_power > 0:
        # Positive means importing from the grid
        grid_text = watts_abs(grid_power)
        grid_label_color = red

        if grid_power > 100:
            arrow_color = red
        else:
            arrow_color = grey

        draw_horizontal_arrow(
            draw,
            23,
            40,
            "right",
            arrow_color,
        )

    else:
        # Negative means exporting to the grid
        grid_text = watts_abs(grid_power)
        grid_label_color = green

        if grid_power < -100:
            arrow_color = green
        else:
            arrow_color = grey

        draw_horizontal_arrow(
            draw,
            23,
            40,
            "left",
            arrow_color,
        )

    draw_grid_icon(draw, 2, 33, grid_icon_color)
    
    if grid_power is not None and grid_power >= 1000:
        grid_value_color = red

    draw.text(
        (5, 53), # LEFT,TOP
        grid_text,
        fill=grid_value_color,
        font=FONT_VALUE,
    )

    #                       #
    #  Right-middle: HOUSE  #
    #                       #
    draw_house_icon(draw, 90, 33, white)
    
    house_power = values["house"]
    if house_power is not None and house_power >= 1000:
        house_value_color = red
    else:
        house_value_color = white
    
    draw.text(
        (75, 53),
        watts(values["house"]),
        fill=house_value_color,
        font=FONT_VALUE,
    )

    #                        #
    # Center-bottom: BATTERY #
    #                        #
    battery_power = values["battery_power"]

    if battery_power is None:
        battery_text = "--"
        battery_label_color = white

    if battery_power is None:
        # Skip arrow on zero color
        battery_text = watts_abs(battery_power)
        battery_label_color = idle_color

    elif battery_power < 0:
        # Negative means charging
        battery_text = watts_abs(battery_power)
        battery_label_color = white

        if battery_power < -100:
            arrow_color = green
        else:
            arrow_color = grey

        draw_vertical_arrow(
            draw,
            29,
            85,
            "down",
            arrow_color,
        )

    elif battery_power > 0:
        # Positive means discharging
        battery_text = watts_abs(battery_power)
        battery_label_color = white

        if battery_power > 100:
            arrow_color = red
        else:
            arrow_color = grey

        draw_vertical_arrow(
            draw,
            29,
            85,
            "up",
            arrow_color,
        )

    else:
        battery_text = "0 W"
        battery_label_color = white
        
    if battery_power is not None and battery_power >= 1000:
        battery_value_color = red
    else:
        battery_value_color = white
     
    level = values["battery_level"]   
    if (level < values["battery_limit"]):
        battery_icon_color = idle_color
        battery_icon_color = idle_color
    else:
        battery_icon_color = white

    draw_battery_icon(draw, 42, 85, battery_icon_color)

    draw.text(
        (64, 79),
        battery_text,
        fill=battery_value_color,
        font=FONT_SMALL,
    )
    
    level = values["battery_level"]
    if level is not None and level >= 0:
        battery_level_color = white
    else:
        battery_level_color = red
    
    if (level < values["battery_limit"]):
        battery_level_color = idle_color  

    # Battery percentage
    level = values["battery_level"]
    if level is not None:
        draw.text(
            (64, 90),
            f"{level:.0f}%",
            fill=battery_level_color,
            font=FONT_VALUE,
        )

    # Battery runtime
    runtime_text = format_runtime(values["battery_runtime"])
    draw.text(
        (50, 110),
        runtime_text,
        fill=idle_color,
        font=FONT_TINY,
    )

    # END
    LCD.display(image)
    

def read_values():
    values = {}

    for name, entity_id in SENSORS.items():
        try:
            values[name] = get_state(entity_id)
        except requests.RequestException:
            values[name] = None

    return values


def main():
    while True:
        try:
            values = read_values()
            draw_dashboard(values)
        except Exception as error:
            draw_error(error)

        time.sleep(UPDATE_SECONDS)


if __name__ == "__main__":
    main()
