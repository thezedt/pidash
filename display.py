#!/usr/bin/env python3
"""Rendering the dashboard (and the error screen) onto the LCD."""

from PIL import Image, ImageDraw

import colors
import fonts
import formatting
import icons


def draw_error(lcd, error):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    draw.text((5, 5), "PI Dash", fill="white", font=fonts.FONT_SMALL)
    draw.text((5, 22), "Connection error", fill="red", font=fonts.FONT_SMALL)

    message = str(error).replace("\n", " ")
    draw.text((5, 40), message[:21], fill="white", font=fonts.FONT_SMALL)
    draw.text((5, 55), message[21:42], fill="white", font=fonts.FONT_SMALL)
    draw.text((5, 70), message[42:64], fill="white", font=fonts.FONT_SMALL)
    draw.text((5, 85), message[64:86], fill="white", font=fonts.FONT_SMALL)

    lcd.display(image)


def draw_dashboard(lcd, values):
    image = Image.new("RGB", (128, 128), "black")
    draw = ImageDraw.Draw(image)

    #                     #
    #     Top: SOLAR      #
    #                     #
    solar_power = values["solar"]

    # handle value length
    if len(formatting.watts(values["solar"])) > 3:
        offset = 4
    else:
        offset = 0

    solar_color = colors.active_color(
        solar_power, 100, colors.SOLAR_ACTIVE_COLOR, colors.SOLAR_IDLE_COLOR
    )

    icons.draw_solar_icon(draw, 36 - offset * 2, 6, solar_color)

    formatting.text_center(
        draw,
        (72 + offset, 8),  # LEFT,TOP
        formatting.watts(values["solar"]),
        solar_color,
        fonts.FONT_VALUE,
    )

    #                     #
    #  Left-middle: GRID  #
    #                     #
    grid_power = values["grid_power"]
    grid_icon_color = colors.WHITE
    grid_value_color = colors.WHITE

    if grid_power is None:
        # invalid data
        grid_text = "--"
        grid_label_color = colors.IDLE_COLOR
        grid_icon_color = colors.IDLE_COLOR
        grid_value_color = colors.IDLE_COLOR

    elif grid_power == 0:
        # Skip arrow on zero grid
        grid_text = formatting.watts_abs(grid_power)
        grid_label_color = colors.IDLE_COLOR
        grid_icon_color = colors.IDLE_COLOR
        grid_value_color = colors.IDLE_COLOR

    elif grid_power > 0:
        # Positive means importing from the grid
        grid_text = formatting.watts_abs(grid_power)
        grid_label_color = colors.RED

        arrow_color = colors.active_color(
            grid_power, 100, colors.RED, colors.GREY, strict=True
        )

        icons.draw_horizontal_arrow(draw, 23, 40, "right", arrow_color)

    else:
        # Negative means exporting to the grid
        grid_text = formatting.watts_abs(grid_power)
        grid_label_color = colors.GREEN

        arrow_color = colors.active_color(
            grid_power, 100, colors.GREEN, colors.GREY, strict=True
        )

        icons.draw_horizontal_arrow(draw, 23, 40, "left", arrow_color)

    icons.draw_grid_icon(draw, 2, 33, grid_icon_color)

    grid_value_color = colors.over_limit_color(
        grid_power, 1000, colors.RED, grid_value_color
    )

    draw.text(
        (5, 53),  # LEFT,TOP
        grid_text,
        fill=grid_value_color,
        font=fonts.FONT_VALUE,
    )

    #                       #
    #  Right-middle: HOUSE  #
    #                       #
    icons.draw_house_icon(draw, 90, 33, colors.WHITE)

    house_power = values["house"]
    house_value_color = colors.over_limit_color(
        house_power, 1000, colors.RED, colors.WHITE
    )

    draw.text(
        (75, 53),
        formatting.watts(values["house"]),
        fill=house_value_color,
        font=fonts.FONT_VALUE,
    )

    #                        #
    # Center-bottom: BATTERY #
    #                        #
    battery_power = values["battery_power"]

    if battery_power is None:
        # Skip arrow on zero color
        battery_text = formatting.watts_abs(battery_power)
        battery_label_color = colors.IDLE_COLOR

    elif battery_power < 0:
        # Negative means charging
        battery_text = formatting.watts_abs(battery_power)
        battery_label_color = colors.WHITE

        arrow_color = colors.active_color(
            battery_power, 100, colors.GREEN, colors.GREY, strict=True
        )

        icons.draw_vertical_arrow(draw, 29, 85, "down", arrow_color)

    elif battery_power > 0:
        # Positive means discharging
        battery_text = formatting.watts_abs(battery_power)
        battery_label_color = colors.WHITE

        arrow_color = colors.active_color(
            battery_power, 100, colors.RED, colors.GREY, strict=True
        )

        icons.draw_vertical_arrow(draw, 29, 85, "up", arrow_color)

    else:
        battery_text = "0 W"
        battery_label_color = colors.WHITE

    battery_value_color = colors.over_limit_color(
        battery_power, 1000, colors.RED, colors.WHITE
    )

    level = values["battery_level"]
    battery_limit = values["battery_limit"]

    if level < battery_limit:
        battery_icon_color = colors.IDLE_COLOR
    else:
        battery_icon_color = colors.WHITE

    icons.draw_battery_icon(draw, 42, 85, battery_icon_color)

    draw.text(
        (64, 79),
        battery_text,
        fill=battery_value_color,
        font=fonts.FONT_SMALL,
    )

    if level is not None and level >= 0:
        battery_level_color = colors.WHITE
    else:
        battery_level_color = colors.RED

    if level < battery_limit:
        battery_level_color = colors.IDLE_COLOR

    # Battery percentage
    if level is not None:
        draw.text(
            (64, 90),
            f"{level:.0f}%",
            fill=battery_level_color,
            font=fonts.FONT_VALUE,
        )

    # Battery runtime
    runtime_text = formatting.format_runtime(values["battery_runtime"])
    draw.text(
        (50, 110),
        runtime_text,
        fill=colors.IDLE_COLOR,
        font=fonts.FONT_TINY,
    )

    # END
    lcd.display(image)
