#!/usr/bin/env python3
"""Individual dashboard screens. Screen 1 (Solar) is the existing dashboard;
screens 2-4 are placeholders until their content is defined."""

import dash_setup
import dash_helpers

SCREEN_NAMES = ["Solar", "Temps", "Extras", "Spring"]
SCREEN_COUNT = len(SCREEN_NAMES)


def draw_screen(draw, index, values, font_tiny, font_small, font_value, font_condensed):
    if index == 0:
        draw_solar_screen(draw, values, font_tiny, font_small, font_value)
    elif index == 1:
        draw_temps_screen(draw, values, font_tiny, font_small, font_value, font_condensed)
    else:
        draw_placeholder_screen(draw, SCREEN_NAMES[index], font_value)


def draw_solar_screen(draw, values, font_tiny, font_small, font_value):

    ########################     Top: SOLAR      ########################
    ########################                     ########################
    ########################                     ########################

    solar_power = values["solar"]

    # handle value length
    if len(dash_helpers.watts(values["solar"])) > 3:
        offset = 4
    else:
        offset = 0
    
    solar_pos_x = 36	
    solar_pox_y = 3

    solar_color = dash_helpers.active_color(
        solar_power, 100, dash_setup.SOLAR_ACTIVE_COLOR, dash_setup.SOLAR_IDLE_COLOR
    )

    dash_helpers.draw_solar_icon(draw, solar_pos_x - offset * 2, solar_pox_y, solar_color)

    dash_helpers.text_center(
        draw,
        (solar_pos_x+36 + offset, solar_pox_y+2),  # LEFT,TOP
        dash_helpers.watts(values["solar"]),
        solar_color,
        font_value,
    )
    
    dash_helpers.text_center(
        draw,
        (solar_pos_x+29, solar_pox_y+18),  # LEFT,TOP
        dash_helpers.volts(values["grid_voltage"]),
        dash_setup.WHITE,
        font_tiny,
    )

    ########################                     ########################
    #############   Left-middle: GRID            ########################
    ########################                     ########################

    grid_power = values["grid_power"]
    grid_icon_color = dash_setup.WHITE
    grid_value_color = dash_setup.WHITE
    
    grid_pos_x = 5
    grid_pos_y = 35

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

        dash_helpers.draw_horizontal_arrow(draw, grid_pos_x+20, grid_pos_y+7, "right", arrow_color)

    else:
        # Negative means exporting to the grid
        grid_text = dash_helpers.watts_abs(grid_power)
        grid_label_color = dash_setup.GREEN

        arrow_color = dash_helpers.active_color(
            grid_power, 100, dash_setup.GREEN, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_horizontal_arrow(draw, grid_pos_x+20, grid_pos_y+7, "left", arrow_color)

    dash_helpers.draw_grid_icon(draw, grid_pos_x, grid_pos_y, grid_icon_color)

    grid_value_color = dash_helpers.over_limit_color(
        grid_power, 1000, dash_setup.RED, grid_value_color
    )

    draw.text(
        (grid_pos_x, grid_pos_y+20),  # LEFT,TOP
        grid_text,
        fill=grid_value_color,
        font=font_value,
    )

    ########################                       ########################
    ########################          Right-middle: HOUSE  ################
    ########################                       ########################

    house_power = values["house"]
    house_value_color = dash_helpers.over_limit_color(
        house_power, 1000, dash_setup.RED, dash_setup.WHITE
    )

    # handle value length
    if values["solar"] >= 2000:
        offset = -3
    else:
        offset = 0

    house_pos_x = 75
    house_pos_y = 35

    dash_helpers.draw_house_icon(draw, house_pos_x+15, house_pos_y, dash_setup.WHITE)

    draw.text(
        (house_pos_x-offset, house_pos_y+20),
        dash_helpers.watts(values["house"]),
        fill=house_value_color,
        font=font_value,
    )

    ########################                        ########################
    ########################                        ########################
    ######################## Center-bottom: BATTERY ########################

    battery_power = values["battery_power"]

    batt_pos_x = 29
    batt_pos_y = 75

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

        dash_helpers.draw_vertical_arrow(draw, batt_pos_x, batt_pos_y+6, "down", arrow_color)

    elif battery_power > 0:
        # Positive means discharging
        battery_text = dash_helpers.watts_abs(battery_power)
        battery_label_color = dash_setup.WHITE

        arrow_color = dash_helpers.active_color(
            battery_power, 100, dash_setup.RED, dash_setup.GREY, strict=True
        )

        dash_helpers.draw_vertical_arrow(draw, batt_pos_x, batt_pos_y+6, "up", arrow_color)

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

    dash_helpers.draw_battery_icon(draw, batt_pos_x+13, batt_pos_y+6, battery_icon_color)

    draw.text(
        (batt_pos_x+35, batt_pos_y+1),
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
            (batt_pos_x+35, batt_pos_y+12),
            f"{level:.0f}%",
            fill=battery_level_color,
            font=font_value,
        )

    # Battery runtime
    runtime_text = dash_helpers.format_runtime(values["battery_runtime"])
    draw.text(
        (batt_pos_x+21, batt_pos_y+27),
        runtime_text,
        fill=dash_setup.IDLE_COLOR,
        font=font_tiny,
    )
    

    ########################                        ########################
    ########################    2: TEMPS SCREEN     ########################
    ########################                        ########################

def draw_temps_screen(draw, values, font_tiny, font_small, font_value, font_condensed):
    # To add a future value: append one row here (label, sensor key, unit
    # type, warn threshold). Set warn to None to disable it - it only
    # applies to "temp" rows, coloring the value red above that threshold.
    # Temp values below 0 always render blue, regardless of warn.
    rows = [
        ("Inv.", "inverter_temp", "temp", 42),
        ("BMS", "battery_bms_temp", "temp", 45),
        ("Bat.", "battery_avg_temp", "temp", 42),
        ("Pod", "attic_temp", "temp", 50),
        ("Afara", "outside_temp", "temp", 27),
        ("Afara", "outside_hum", "percent", None),
        ("Cam.", "pantry_temp", "temp", 20),
        ("Cam.", "pantry_hum", "percent", None),
    ]

    units = {"temp": "\u00b0C", "percent": "%"}

    def format_measurement(value, unit_type):
        if value is None:
            return "--"
        return f"{value:.1f}{units[unit_type]}"

    def value_color(value, unit_type, warn):
        if unit_type == "temp" and value is not None:
            if value < 0:
                return dash_setup.BLUE
            if warn is not None and value > warn:
                return dash_setup.RED
        return dash_setup.LIGHT_GREY

    top = 2
    available_height = 116  # leaves room for the screen-indicator dots
    col_x = [2, 66]
    col_right = [62, 126]

    rows_per_col = -(-len(rows) // 2)  # ceil division, supports up to ~7 rows/14 values
    row_height = max(12, available_height // rows_per_col)

    for index, (label, sensor_key, unit_type, warn) in enumerate(rows):
        column = index // rows_per_col
        row = index % rows_per_col

        row_top = top + row * row_height
        text_y = row_top + (row_height - 9) / 2

        x = col_x[column]
        draw.text((x, text_y), label, fill=dash_setup.WHITE, font=font_condensed)

        value = values.get(sensor_key)
        text = format_measurement(value, unit_type)
        text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]

        draw.text(
            (col_right[column] - text_width, text_y),
            text,
            fill=value_color(value, unit_type, warn),
            font=font_condensed,
        )

    ########################                        ########################
    ########################    3: EXTRAS SCREEN    ########################
    ########################                        ########################

# TO DO

    ########################                        ########################
    ########################    4: SPRING SCREEN    ########################
    ########################                        ########################

# TO DO

def draw_placeholder_screen(draw, name, font_value):
    dash_helpers.text_center(draw, (64, 60), name, dash_setup.WHITE, font_value)
