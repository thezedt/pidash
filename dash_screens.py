#!/usr/bin/env python3
"""Individual dashboard screens. Screen 1 (Solar) is the existing dashboard;
screens 2-4 are placeholders until their content is defined."""

import dash_setup
import dash_helpers

SCREEN_NAMES = ["Solar", "Temps", "Extras", "Spring"]
SCREEN_COUNT = len(SCREEN_NAMES)


def draw_screen(draw, index, values, font_tiny, font_small, font_value):
    if index == 0:
        draw_solar_screen(draw, values, font_tiny, font_small, font_value)
    elif index == 1:
        draw_temps_screen(draw, values, font_tiny, font_small, font_value)
    else:
        draw_placeholder_screen(draw, SCREEN_NAMES[index], font_value)


def draw_solar_screen(draw, values, font_tiny, font_small, font_value):
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
        font_value,
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
        font=font_value,
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
        font=font_value,
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
        font=font_small,
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
            font=font_value,
        )

    # Battery runtime
    runtime_text = dash_helpers.format_runtime(values["battery_runtime"])
    draw.text(
        (50, 88),
        runtime_text,
        fill=dash_setup.IDLE_COLOR,
        font=font_tiny,
    )


def draw_temps_screen(draw, values, font_tiny, font_small, font_value):
    # To add a future value: append one row here (icon key, label, sensor
    # key, unit type). Nothing else needs to change. Keep labels to ~3-4
    # characters - that's what reliably fits a 64px-wide column at this font.
    rows = [
        ("rounded_rect", "Inv", "inverter_temp", "temp"),
        ("chip", "BMS", "battery_bms_temp", "temp"),
        ("battery", "Bat", "battery_avg_temp", "temp"),
        ("thermometer", "Out", "outside_temp", "temp"),
        ("percent", "Out", "outside_hum", "percent"),
        ("thermometer", "Pan", "pantry_temp", "temp"),
        ("percent", "Pan", "pantry_hum", "percent"),
        ("thermometer", "Att", "attic_temp", "temp"),
    ]

    icons = {
        "rounded_rect": dash_helpers.draw_icon_rounded_rect,
        "chip": dash_helpers.draw_icon_chip,
        "battery": dash_helpers.draw_icon_battery,
        "thermometer": dash_helpers.draw_icon_thermometer,
        "percent": dash_helpers.draw_icon_percent,
    }

    units = {"temp": "\u00b0C", "percent": "%"}

    def format_measurement(value, unit_type):
        if value is None:
            return "--"
        return f"{value:.1f}{units[unit_type]}"

    icon_size = 7
    icon_gap = 2
    value_gap = 3
    top = 2
    available_height = 116  # leaves room for the screen-indicator dots
    col_x = [2, 66]

    rows_per_col = -(-len(rows) // 2)  # ceil division, supports up to ~7 rows/14 values
    row_height = max(12, available_height // rows_per_col)

    for index, (icon_key, label, sensor_key, unit_type) in enumerate(rows):
        column = index // rows_per_col
        row = index % rows_per_col

        row_top = top + row * row_height
        icon_y = row_top + (row_height - icon_size) / 2
        text_y = row_top + (row_height - 9) / 2

        x = col_x[column]
        label_x = x + icon_size + icon_gap

        icons[icon_key](draw, x, icon_y, icon_size, dash_setup.WHITE)
        draw.text((label_x, text_y), label, fill=dash_setup.WHITE, font=font_tiny)

        label_width = draw.textbbox((0, 0), label, font=font_tiny)[2]
        value_x = label_x + label_width + value_gap

        text = format_measurement(values.get(sensor_key), unit_type)
        draw.text((value_x, text_y), text, fill=dash_setup.IDLE_COLOR, font=font_tiny)


def draw_placeholder_screen(draw, name, font_value):
    dash_helpers.text_center(draw, (64, 60), name, dash_setup.IDLE_COLOR, font_value)
