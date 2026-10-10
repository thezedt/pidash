#!/usr/bin/env python3
"""Individual dashboard screens"""

import dash_setup
import dash_helpers

SCREEN_NAMES = ["Solar", "Temps", "Params", "Spring", "Energy"]
SCREEN_COUNT = len(SCREEN_NAMES)

INVERTER_TEMP_WARN = 42
BATT_BMS_TEMP_WARN = 45
BATT_AVG_TEMP_WARN = 42

# number of pixels to offset value from label on two-row display
VALUE_OFFSET = 22


def draw_screen(draw, index, values, font_tiny, font_small, font_value, font_condensed, layout="stacked"):
    if index == 0:
        draw_solar_screen(draw, values, font_tiny, font_small, font_value)
    elif index == 1:
        draw_temps_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout)
    elif index == 2:
        draw_params_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout)
    elif index == 3:
        draw_spring_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout)
    elif index == 4:
        draw_energy_screen(draw, values, font_tiny, font_small, font_value)
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
    
    solar_pos_x = 31
    solar_pos_y = 3

    solar_color = dash_helpers.active_color(
        solar_power, 100, dash_setup.SOLAR_ACTIVE_COLOR, dash_setup.SOLAR_IDLE_COLOR
    )

    dash_helpers.draw_solar_icon(draw, solar_pos_x - offset * 2, solar_pos_y, solar_color)

    dash_helpers.text_center(
        draw,
        (solar_pos_x+36 + offset, solar_pos_y+2),  # LEFT,TOP
        dash_helpers.watts(values["solar"]),
        solar_color,
        font_value,
    )

    grid_voltage_color = dash_helpers.over_limit_color(
        values["grid_voltage"], 248, dash_setup.RED, dash_setup.WHITE
    )
    
    dash_helpers.text_center(
        draw,
        (solar_pos_x+29, solar_pos_y+18),  # LEFT,TOP
        dash_helpers.volts(values["grid_voltage"]),
        grid_voltage_color,
        font_tiny,
    )

    try:
        inverter_temp = float(values.get("inverter_temp"))
    except (TypeError, ValueError):
        inverter_temp = None

    if inverter_temp is not None and inverter_temp >= INVERTER_TEMP_WARN:
        dash_helpers.draw_thermometer_warning(
            draw,
            x=solar_pos_x - offset * 2 + 10,
            y=solar_pos_y,
            color=dash_setup.WARNING_COLOR,
            width=6,
            height=18,
        )

    fan_1_on = str(values.get("inverter_fans_1")).lower() == "on"
    fan_2_on = str(values.get("inverter_fans_2")).lower() == "on"

    if fan_1_on or fan_2_on:
        dash_helpers.draw_fan_icon(
            draw,
            solar_pos_x - offset * 2 - 20,
            solar_pos_y + 3,
            dash_setup.BLUE,
        )

    ########################                     ########################
    #############   Left-middle: GRID            ########################
    ########################                     ########################

    grid_power = values["grid_power"]
    grid_icon_color = dash_setup.WHITE
    grid_value_color = dash_setup.WHITE
    
    grid_pos_x = 0
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

    grid_icon_color = dash_helpers.over_limit_color(
        grid_power, 9999, dash_setup.WHITE, dash_setup.WHITE
    )

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
    if house_power is not None and house_power >= 1000:
        offset = -4
    else:
        offset = 0

    house_pos_x = 75
    house_pos_y = 35

    dash_helpers.draw_house_icon(draw, house_pos_x+15, house_pos_y, dash_setup.WHITE)

    draw.text(
        (house_pos_x+offset, house_pos_y+20),
        dash_helpers.watts(house_power),
        fill=house_value_color,
        font=font_value,
    )

    ########################                        ########################
    ########################                        ########################
    ######################## Center-bottom: BATTERY ########################

    battery_power = values["battery_power"]

    batt_pos_x = 25
    batt_pos_y = 75

    # Battery label and arrow
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

        if battery_power < 30:
            battery_label_color = dash_setup.IDLE_COLOR

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
    battery_backup_level = values["battery_backup_level"]

    if level < battery_backup_level or (battery_power is not None and abs(battery_power) < 30):
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
        if battery_power is not None and abs(battery_power) < 30: # cover both directions for low power
            battery_level_color = dash_setup.IDLE_COLOR
    else:
        battery_level_color = dash_setup.RED

    if level < battery_backup_level:
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
        (batt_pos_x+15, batt_pos_y+27),
        runtime_text,
        fill=dash_setup.IDLE_COLOR,
        font=font_tiny,
    )

    try:
        battery_avg_temp = float(values.get("battery_avg_temp"))
    except (TypeError, ValueError):
        battery_avg_temp = None
    try:
        battery_bmps_temp = float(values.get("battery_bms_temp"))
    except (TypeError, ValueError):
        battery_bmps_temp = None

    if battery_avg_temp is not None and battery_bmps_temp is not None and ( battery_bmps_temp >= BATT_BMS_TEMP_WARN or battery_avg_temp >= BATT_AVG_TEMP_WARN):
        dash_helpers.draw_thermometer_warning(
            draw,
            x=batt_pos_x + 24,
            y=batt_pos_y + 5,
            color=dash_setup.WARNING_COLOR,
            width=6,
            height=18,
        )

    ########################                        ########################
    ########################    2: TEMPS SCREEN     ########################
    ########################                        ########################

def draw_temps_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout="stacked"):
    # To add a future value: append one row here (label, sensor key, unit
    # type, warn threshold). Set warn to None to disable it - it only
    # applies to "temp" rows, coloring the value red above that threshold.
    # Temp values below 0 always render blue, regardless of warn.
    rows = [
        #"12345678901"
        #("Temp. Inv.", "inverter_temp", "temp", INVERTER_TEMP_WARN, None),
        #("Temp. BMS", "battery_bms_temp", "temp", BATT_BMS_TEMP_WARN, None),
        #("Temp. Bat.", "battery_avg_temp", "temp", BATT_AVG_TEMP_WARN, None),
        #("Temp. PI", "pi_temp", "temp", 50, None),
        ("Afară", "outside_temp", "temp", 27, None),
        ("Um. Afară", "outside_hum", "percent", 80, None),
        ("Cămară", "pantry_temp", "temp", 21, None),
        ("Um. Cămară", "pantry_hum", "percent", 80, None),
        ("Hol", "hallway_temp", "temp", 27, None),
        ("Grădină", "outside2_temp", "temp", 27, None),
        ("Pod", "attic_temp", "temp", 45, None),
        ("Bicaz", "bicaz_temp", "temp", 27, None),
    ]

    units = {"temp": "\u00b0C", "percent": "%"}

    def format_measurement(value, unit_type):
        if value is None:
            return "--"
        return f"{value:.1f}{units[unit_type]}"

    top = 2
    available_height = 116  # leaves room for the screen-indicator dots
    col_x = [0, 66]
    col_right = [60, 126]

    rows_per_col = -(-len(rows) // 2)  # ceil division, supports up to ~7 rows/14 values
    row_height = max(12, available_height // rows_per_col)

    for index, x_label, label_y, x_value, value_y, align in dash_helpers.layout_positions(len(rows), layout):
        label, sensor_key, unit_type, warn, default = rows[index]
        value = values.get(sensor_key)

        draw.text((x_label, label_y), label, fill=dash_setup.WHITE, font=font_condensed)

        text = format_measurement(value, unit_type)
        color = dash_helpers.value_color(value, default=default, value_type=unit_type, warn=warn)

        if align == "right":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text((x_value - text_width, value_y), text, fill=color, font=font_condensed)
        elif align == "rightmost":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text(
                (x_value + 60 - text_width, value_y),
                text,
                fill=color,
                font=font_condensed,
            )
        else:
            draw.text((x_value + VALUE_OFFSET, value_y), text, fill=color, font=font_condensed)

    ########################                        ########################
    ########################    3: PARAMS SCREEN    ########################
    ########################                        ########################

def draw_params_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout="stacked"):
    # To add a future value: append one row here (label, sensor key, unit,
    # defaultm tyoe). If the live value differs from `default`, the value
    # renders green; otherwise LIGHT_GREY (same as Temps' un-warned
    # default). Set default to None to disable this check for that row.
    rows = [
        #"12345678901"
        ("Temp. Inv.", "inverter_temp", "\u00b0C", INVERTER_TEMP_WARN, "temp"),
        ("Temp. BMS", "battery_bms_temp", "\u00b0C", BATT_BMS_TEMP_WARN, "temp"),
        ("Temp. Bat.", "battery_avg_temp", "\u00b0C", BATT_AVG_TEMP_WARN, "temp"),
        ("Temp. PI", "pi_temp", "\u00b0C", 50, "temp"),
        ("Limită Inv.", "inverter_derating", "W", 5500, ""),
        ("Limită Bat.", "battery_backup_level", "%", 35, ""),
        ("Încărc. Bat.", "battery_charge_power", "W", 5000, ""),
        ("Desc. Bat.", "battery_discharge_power", "W", 5000, ""),
    ]

    def format_measurement(value, unit):
        if value is None:
            return "--"
        if unit == "W":
            # Watts: no decimals. Auto-switches to kW above 1000, with 1 decimal.
            if abs(value) >= 1000:
                return f"{value / 1000:.1f}kW"
            return f"{value:.0f}W"
        return f"{value:.1f}{unit}"

    for index, x_label, label_y, x_value, value_y, align in dash_helpers.layout_positions(len(rows), layout):
        label, sensor_key, unit, default, value_type = rows[index]
        value = values.get(sensor_key)

        draw.text((x_label, label_y), label, fill=dash_setup.WHITE, font=font_condensed)

        text = format_measurement(value, unit)
        color = dash_helpers.value_color(value, default=default, value_type=value_type)

        if align == "right":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text((x_value - text_width, value_y), text, fill=color, font=font_condensed)
        elif align == "rightmost":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text(
                (x_value + 60 - text_width, value_y),
                text,
                fill=color,
                font=font_condensed,
            )
        else:
            draw.text((x_value + VALUE_OFFSET, value_y), text, fill=color, font=font_condensed)

    ########################                        ########################
    ########################    4: SPRING SCREEN    ########################
    ########################                        ########################

def draw_spring_screen(draw, values, font_tiny, font_small, font_value, font_condensed, layout="stacked"):
    # Each row: (label, sensor key, formatter). formatter(value) returns
    # (text, color) to draw on the right. Use formatter=None for a row
    # that needs custom drawing instead of plain text (see "Stare" below).
    # To add a future value: append a row + a small formatter function.

    def battery_fmt(value):
        if value is None:
            return "--", dash_setup.LIGHT_GREY
        color = dash_setup.RED if value < 35 else dash_setup.LIGHT_GREY
        return f"{value:.1f}%", color

    def km_fmt(value):
        if value is None:
            return "--", dash_setup.LIGHT_GREY
        color = dash_setup.RED if value < 50 else dash_setup.LIGHT_GREY
        return f"{value:.0f}km", color


    def watts_fmt(value):
        return dash_helpers.watts(value), dash_setup.LIGHT_GREY

    def amps_fmt(value):
        if value is None:
            return "--", dash_setup.LIGHT_GREY
        return f"{value:.1f}A", dash_setup.LIGHT_GREY

    def raw_string_fmt(value):
        if value is None or value == "0h 0m":
            return "--", dash_setup.LIGHT_GREY
        return str(value), dash_setup.LIGHT_GREY

    def kwh_fmt(value):
        if value is None:
            return "--", dash_setup.LIGHT_GREY
        return f"{value:.1f}kWh", dash_setup.LIGHT_GREY

    def temp_fmt(value):
        if value is None:
            return "--", dash_setup.LIGHT_GREY
        color = dash_helpers.value_color(value, value_type="temp", warn=35)
        return f"{value:.1f}\u00b0C", color

    rows = [
        #"12345678901"
        ("Baterie", "spring_battery_level", battery_fmt),
        ("Putere Înc.", "spring_charge_power", watts_fmt),
        ("Curent Înc.", "spring_charge_current", amps_fmt),
        ("Autonomie", "spring_autonomy", km_fmt),
        #("Est. azi", "solar_estimate_today_r", kwh_fmt),
        ("Stare", "spring_charge_status", None),  # special-cased below: "Charging" / "-"
        ("KWh de înc.", "spring_kwh_to_limit", kwh_fmt),
        ("Timp Înc.", "spring_time_to_limit", raw_string_fmt),
        ("Temperatură", "spring_temp", temp_fmt),
        #("Est. mâine", "solar_estimate_tomorrow", kwh_fmt),
    ]

    for index, x_label, label_y, x_value, value_y, align in dash_helpers.layout_positions(len(rows), layout):
        label, sensor_key, formatter = rows[index]
        value = values.get(sensor_key)

        draw.text((x_label, label_y), label, fill=dash_setup.WHITE, font=font_condensed)

        if formatter is None:
            # "Stare": "Charging" in green while charging ("on"), "--" otherwise
            if value == "on":
                text = "Încărcare"
                text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]

                if align == "right":
                    x = x_value - text_width
                else:
                    x = x_value + VALUE_OFFSET - 10

                draw.text( (x, value_y), text, fill=dash_setup.GREEN, font=font_condensed )
            else:
                if align == "right":
                    draw.text( (x_value - 6, value_y), "--", fill=dash_setup.LIGHT_GREY, font=font_condensed )
                else:
                    draw.text( (x_value + VALUE_OFFSET, value_y), "--", fill=dash_setup.LIGHT_GREY, font=font_condensed )

            continue

        text, color = formatter(value)
        if align == "right":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text((x_value - text_width, value_y), text, fill=color, font=font_condensed)
        elif align == "rightmost":
            text_width = draw.textbbox((0, 0), text, font=font_condensed)[2]
            draw.text(
                (x_value + 60 - text_width, value_y),
                text,
                fill=color,
                font=font_condensed,
            )
        else:
            draw.text((x_value + VALUE_OFFSET, value_y), text, fill=color, font=font_condensed)

    ########################                        ########################
    ########################    5: ENERGY SCREEN     ########################
    ########################                        ########################

def draw_energy_screen(draw, values, font_tiny, font_small, font_value):
    # Cumulative energy for the day, cloned from the Solar screen's
    # top/left/right/bottom layout. No arrows and no color-by-value here -
    # just fixed colors as specified. Positions copied as-is from
    # draw_solar_screen; adjust labels/positions later if anything overlaps.

    ######################## Top: SOLAR ########################

    solar_pos_x = 20
    solar_pos_y = 3

    dash_helpers.draw_solar_icon(draw, solar_pos_x, solar_pos_y, dash_setup.SOLAR_ACTIVE_COLOR)

    dash_helpers.text_center(
        draw,
        (solar_pos_x + 56, solar_pos_y + 2),  # LEFT,TOP
        dash_helpers.kwh(values.get("energy_solar_kwh")),
        dash_setup.SOLAR_ACTIVE_COLOR,
        font_value,
    )

    ######################## Left-middle: GRID ########################

    grid_pos_x = 0
    grid_pos_y = 35

    dash_helpers.draw_grid_icon(draw, grid_pos_x, grid_pos_y, dash_setup.WHITE)

    draw.text(
        (grid_pos_x, grid_pos_y + 20),  # LEFT,TOP
        dash_helpers.kwh(values.get("energy_grid_import_kwh"),"\u25BA "), # →
        fill=dash_setup.PURPLE,
        font=font_small,
    )

    draw.text(
        (grid_pos_x, grid_pos_y + 34),  # second line, below the first
        dash_helpers.kwh(values.get("energy_grid_export_kwh"),"\u25C4 "), # ←
        fill=dash_setup.GREEN,
        font=font_small,
    )

    ######################## Right-middle: HOUSE ########################

    house_pos_x = 75
    house_pos_y = 30
    right_edge_x = 127  # Last pixel of a 128px-wide screen

    dash_helpers.draw_house_icon(draw, house_pos_x + 25, house_pos_y, dash_setup.WHITE)

    house_text = dash_helpers.kwh(values.get("energy_house_kwh"))

    bbox = draw.textbbox((0, 0), house_text, font=font_value)
    text_width = bbox[2] - bbox[0]

    draw.text(
        (right_edge_x - text_width, house_pos_y + 20),
        house_text,
        fill=dash_setup.WHITE,
        font=font_value,
    )

    ######################## Center-bottom: BATTERY ########################

    batt_pos_x = 15
    batt_pos_y = 85

    dash_helpers.draw_battery_icon(draw, batt_pos_x + 13, batt_pos_y + 6, dash_setup.WHITE)

    draw.text(
        (batt_pos_x + 35, batt_pos_y + 1),
        dash_helpers.kwh(values.get("energy_battery_discharge_kwh"),"\u25BA "), # →
        fill=dash_setup.PURPLE,
        font=font_small,
    )

    draw.text(
        (batt_pos_x + 35, batt_pos_y + 14),  # second line, below the first
        dash_helpers.kwh(values.get("energy_battery_charge_kwh"),"\u25C4 "), # ←
        fill=dash_setup.GREEN,
        font=font_small,
    )

def draw_placeholder_screen(draw, name, font_value):
    dash_helpers.text_center(draw, (64, 60), name, dash_setup.WHITE, font_value)

# FIN