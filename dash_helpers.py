#!/usr/bin/env python3
"""Color-selection helpers, text formatting, and icon/arrow drawing primitives."""

import math
import dash_setup, dash_functions

# -----------------------------
# Color helpers
# -----------------------------


def active_color(value, threshold, active, idle=dash_setup.IDLE_COLOR, strict=False):
    """
    Return `active` when abs(value) crosses `threshold`, else `idle`.

    strict=True uses a ">" comparison (matches the old arrow-color checks),
    strict=False (default) uses ">=" (matches the old solar-color check).
    """
    if value is None:
        return idle

    absolute = abs(value)
    crossed = absolute > threshold if strict else absolute >= threshold

    return active if crossed else idle


def over_limit_color(value, limit, over_color=dash_setup.RED, default_color=dash_setup.WHITE):
    """Return `over_color` if value is at/above `limit`, else `default_color`."""
    if value is not None and value >= limit:
        return over_color
    elif value is not None and abs(value) < 30 :         # abs() to cover both directions for low power
        return dash_setup.IDLE_COLOR
    return default_color


def value_color(value, default=None, value_type="", warn=None):
    """Shared coloring rule for the Temps/Params/Spring screens:

    - value_type == "temp": BLUE below 10 degrees, RED at/above the alert
      threshold (`warn` if given, else `default` - Params reuses its
      set-point field as the threshold), else LIGHT_GREY.
    - otherwise: GREEN if `value` differs from `default` (when `default`
      is given), else LIGHT_GREY.
    """
    if value is None:
        return dash_setup.LIGHT_GREY

    try:
        value = float(value)
    except (TypeError, ValueError):
        return dash_setup.LIGHT_GREY

    if value_type == "temp":
        if value < 10:
            return dash_setup.BLUE

        threshold = warn if warn is not None else default
        if threshold is not None and value >= threshold:
            return dash_setup.RED

        return dash_setup.LIGHT_GREY

    if default is not None:
        try:
            if value != float(default):
                return dash_setup.GREEN
        except (TypeError, ValueError):
            pass

    return dash_setup.LIGHT_GREY

# -----------------------------
# Formatting helpers
# -----------------------------

def volts(value):
    if value is None:
        return "--"

    return f"{value:.1f} V"

def kwh(value,arrow=""):
    if value is None:
        return "--"

    return f"{arrow}{value:.1f} kWh"

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
        return "      \u221e"

    try:
        total_minutes = int(float(minutes))
    except (ValueError, TypeError):
        return "      Err"

    if total_minutes < 0:
        sign = "- "
        total_minutes = abs(total_minutes)
    else:
        sign = "  "

    hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    return f"{sign}{hours}h {remaining_minutes:02d}m"


def text_center(draw, xy, text, fill, font):
    width = draw.textbbox((0, 0), text, font=font)[2]
    draw.text((xy[0] - width / 2, xy[1]), text, fill=fill, font=font)

# -----------------------------
# Layout helpers
# -----------------------------


def two_column_positions(count, top=2, available_height=116, col_x=(2, 66), col_right=(62, 126)):
    """Yield (index, x_label, x_value_right, text_y) laying `count` label/
    value rows out into 2 columns, matching the Temps screen's grid. Row
    height scales down to fit up to ~7 rows (14 items) per screen; the
    bottom margin (available_height) leaves room for the screen-indicator
    dots."""
    rows_per_col = -(-count // 2)  # ceil division
    row_height = max(12, available_height // rows_per_col)

    for index in range(count):
        column = index // rows_per_col
        row = index % rows_per_col
        row_top = top + row * row_height
        text_y = row_top + (row_height - 9) / 2
        yield index, col_x[column], col_right[column], text_y


def two_column_row_blocks(count, top=2, available_height=116, col_x=(2, 66)):
    """Yield (index, x, row_top, row_height) for `count` items laid out in
    2 columns, same grid as two_column_positions. Unlike that function,
    this hands back the full row block instead of one centered text
    baseline, so the caller can stack multiple lines (e.g. label above
    value) inside it - needed when label+value combined are too wide for
    a single 64px-wide line at a readable font size."""
    rows_per_col = -(-count // 2)  # ceil division
    row_height = max(12, available_height // rows_per_col)

    for index in range(count):
        column = index // rows_per_col
        row = index % rows_per_col
        row_top = top + row * row_height
        yield index, col_x[column], row_top, row_height

def layout_positions(count, layout="stacked"):
    """Yield (index, x_label, label_y, x_value, value_y, align) for `count`
    label/value rows, in the same 2-column grid used by the Temps/Params/
    Spring screens. `layout` selects how each row is drawn:

    - "stacked" (default): label above value, both left-aligned. Needed
      when label+value combined are too wide for a single line at a
      readable font size.
    - "single_line": label and value share one line, value right-aligned
      to the column's right edge. More compact, but can overlap if the
      label is too long for the remaining column width.

    `align` is "left" or "right" and tells the caller how to interpret
    `x_value`: for "left", start the value text there; for "right", align
    the value text's right edge against it (subtract its own width)."""
    if layout == "stacked":
        for index, x, row_top, row_height in two_column_row_blocks(count):
            yield index, x, row_top, x, row_top + 12, "left"
    else:
        for index, x_label, x_value_right, text_y in two_column_positions(count):
            yield index, x_label, text_y, x_value_right, text_y, "right"


def draw_vertical_menu(draw, items, selected_index, font):
    """Draw a full-screen vertical list, highlighting `selected_index` with a
    grey background bar. Empty strings in `items` render as blank spacer rows."""
    row_height = 15
    top = 2

    for index, label in enumerate(items):
        y = top + index * row_height

        if index == selected_index:
            draw.rectangle((0, y, 127, y + row_height - 1), fill=dash_setup.GREY)

        if label:
            draw.text((8, y + 2), label, fill=dash_setup.WHITE, font=font)

    # version info at top-right corner
    text = dash_setup.VERSION
    bbox = draw.textbbox( (0, 0), text, font=dash_functions.FONT_TINY )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    margin = 2
    x = dash_setup.LCD_WIDTH - margin - text_width - 3
    y = dash_setup.LCD_HEIGHT - margin - text_height - 2

    draw.text( (x, y), text, fill=dash_setup.GREY, font=dash_functions.FONT_TINY )

def draw_confirmation_screen(draw, action_label, font):
    text = f"{action_label}?"

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (dash_setup.LCD_WIDTH - text_width) // 2
    y = (dash_setup.LCD_HEIGHT - text_height) // 2

    draw.text( (x, y), text, fill=dash_setup.WHITE, font=font )

def draw_screen_indicator_botright(draw, current, total, font):
    """Draw a small 'current/total' box in the bottom-right corner."""
    text = f"{current}/{total}"
    box = draw.textbbox((0, 0), text, font=font)
    padding = 2

    x2, y2 = 126, 126
    x1 = x2 - (box[2] - box[0]) - padding * 2
    y1 = y2 - (box[3] - box[1]) - padding * 2

    draw.rectangle((x1, y1, x2, y2), outline=dash_setup.IDLE_COLOR)
    draw.text((x1 + padding, y1 + padding), text, fill=dash_setup.IDLE_COLOR, font=font)

def draw_screen_indicator_center(draw, current, total, font):
    """Draw a small 'current/total' label centered at the bottom of the screen."""
    text = f"{current}/{total}"
    box = draw.textbbox((0, 0), text, font=font)

    x = 64 - (box[2] - box[0]) / 2
    y = 127 - (box[3] - box[1])

    draw.text((x, y), text, fill=dash_setup.IDLE_COLOR, font=font)

def draw_screen_indicator(draw, current, total, font=None):
    """Draw a row of dots at the bottom-center of the screen; the active
    dot (1-based `current`) is larger and white, the rest are small and grey."""
    small_radius = 1
    large_radius = 2
    spacing = 8
    y = 123
    dot_idle_color = (50, 50, 50)

    total_width = (total - 1) * spacing
    start_x = 64 - total_width / 2

    for index in range(total):
        x = start_x + index * spacing

        if index == current - 1:
            radius = large_radius
            color = dash_setup.WHITE
        else:
            radius = small_radius
            color = dot_idle_color

        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


# -----------------------------
# Simple monochrome-style icons
# -----------------------------


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

def draw_fan_icon_(draw, x, y, color):
    # Icon dimensions: approximately 20x20 pixels, same footprint as
    # draw_solar_icon. 3 curved blades (pie slices) around a small dark
    # hub, so they read as a fan/propeller rather than a solid triangle.
    center_x = x + 9
    center_y = y + 9
    outer_radius = 9
    hub_radius = 2
    blade_span = 50  # degrees of arc per blade

    bbox = (
        center_x - outer_radius, center_y - outer_radius,
        center_x + outer_radius, center_y + outer_radius,
    )

    for start_angle in (270, 30, 150):  # 3 blades, 120 degrees apart
        draw.pieslice(
            bbox, start_angle - blade_span / 2, start_angle + blade_span / 2, fill=color
        )

    draw.ellipse(
        (center_x - hub_radius, center_y - hub_radius, center_x + hub_radius, center_y + hub_radius),
        fill="black",
    )

def draw_fan_icon(draw, x, y, color):
    # Icon dimensions: approximately 20x20 pixels, same footprint as
    # draw_solar_icon. 3 petal-shaped blades (narrow at the hub and tip,
    # wide in the middle) meeting at a shared center - reads as a
    # propeller/fan, unlike flat pie-wedges which look like a radiation
    # trefoil.
    center_x = x + 9
    center_y = y + 9
    length = 8
    half_width = 3

    for angle_deg in (90, 210, 330):  # 3 blades, 120 degrees apart
        angle = math.radians(angle_deg)
        perp_angle = angle + math.radians(90)

        tip_x = center_x + length * math.cos(angle)
        tip_y = center_y - length * math.sin(angle)
        mid_x = center_x + (length * 0.55) * math.cos(angle)
        mid_y = center_y - (length * 0.55) * math.sin(angle)

        dx = half_width * math.cos(perp_angle)
        dy = half_width * math.sin(perp_angle)

        draw.polygon(
            [
                (center_x, center_y),
                (mid_x + dx, mid_y - dy),
                (tip_x, tip_y),
                (mid_x - dx, mid_y + dy),
            ],
            fill=color,
        )

    draw.ellipse(
        (center_x - 2, center_y - 2, center_x + 2, center_y + 2),
        fill=color,
    )

def draw_hourglass_icon(draw, cx, cy, color, width=40, height=50):
    half_w = width // 2
    half_h = height // 2
    top = cy - half_h
    bottom = cy + half_h
    left = cx - half_w
    right = cx + half_w
    cap = 3

    draw.rectangle((left, top, right, top + cap), fill=color)
    draw.rectangle((left, bottom - cap, right, bottom), fill=color)
    draw.polygon([(left, top + cap), (right, top + cap), (cx, cy)], fill=color)
    draw.polygon([(cx, cy), (right, bottom - cap), (left, bottom - cap)], fill=color)

def draw_house_icon_original(draw, x, y, color):
    draw.polygon(
        [(x, y + 8), (x + 9, y), (x + 18, y + 8)],
        fill=color,
    )
    draw.rectangle((x + 3, y + 8, x + 15, y + 18), fill=color)
    draw.rectangle((x + 8, y + 12, x + 11, y + 18), fill="black")
    
def draw_house_icon(draw, x, y, color):
    draw.polygon(
        [(x, y + 8), (x + 9, y), (x + 18, y + 8)],
        fill=color,
    )
    draw.rectangle((x + 3, y + 7, x + 15, y + 18), fill=color)
    draw.rectangle((x + 6, y + 10, x + 12, y + 18), fill="black")

def draw_house_icon_outline(draw, x, y, color):
    draw.polygon(
        [(x, y + 8), (x + 9, y), (x + 18, y + 8)],
        outline=color,
    )
    draw.rectangle((x + 3, y + 8, x + 15, y + 18), outline=color)
    draw.rectangle((x + 8, y + 12, x + 11, y + 18), outline=color)
    
def draw_house_icon_outline2x(draw, x, y, color):
    draw.line((x, y + 8, x + 9, y), fill=color, width=2)
    draw.line((x + 9, y, x + 18, y + 8), fill=color, width=2)
    draw.line((x + 3, y + 8, x + 3, y + 18), fill=color, width=2)
    draw.line((x + 15, y + 8, x + 15, y + 18), fill=color, width=2)
    draw.line((x + 3, y + 18, x + 8, y + 18), fill=color, width=2)
    draw.line((x + 11, y + 18, x + 15, y + 18), fill=color, width=2)
    draw.line((x + 8, y + 12, x + 8, y + 18), fill=color, width=2)
    draw.line((x + 11, y + 12, x + 11, y + 18), fill=color, width=2)

def draw_battery_icon(draw, x, y, color):
    draw.rectangle((x + 2, y + 2, x + 13, y + 17), outline=color)
    draw.rectangle((x + 5, y, x + 10, y + 2), fill=color)
    draw.rectangle((x + 5, y + 5, x + 10, y + 14), outline=color)


def draw_grid_icon(draw, x, y, color):
    draw.line((x + 9, y, x + 5, y + 18), fill=color, width=2)
    draw.line((x + 9, y, x + 13, y + 18), fill=color, width=2)
    draw.line((x + 3, y + 7, x + 15, y + 7), fill=color, width=2)
    draw.line((x + 5, y + 12, x + 13, y + 12), fill=color, width=2)


def draw_power_flow(draw, x, y, value, color, icon, font):
    icon(draw, x, y, color)
    draw.text((x + 23, y + 2), watts(value), fill=color, font=font)


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


# -----------------------------
# Small row icons (Temps screen)
# -----------------------------
# Each draws within an approximately size x size box at (x, y).


def draw_icon_rounded_rect(draw, x, y, size, color):
    draw.rounded_rectangle((x, y, x + size, y + size), radius=2, outline=color)


def draw_icon_chip(draw, x, y, size, color):
    inset = 2
    draw.rectangle((x + inset, y + inset, x + size - inset, y + size - inset), outline=color)

    pin_len = 2
    mid = x + size / 2

    draw.line((mid - 2, y - pin_len, mid - 2, y + inset), fill=color)
    draw.line((mid + 2, y - pin_len, mid + 2, y + inset), fill=color)
    draw.line((mid - 2, y + size - inset, mid - 2, y + size + pin_len), fill=color)
    draw.line((mid + 2, y + size - inset, mid + 2, y + size + pin_len), fill=color)


def draw_icon_battery(draw, x, y, size, color):
    body_top = y + 1
    draw.rectangle((x, body_top, x + size - 2, y + size), outline=color)
    draw.rectangle((x + size - 2, body_top + 2, x + size, y + size - 2), fill=color)


def draw_icon_thermometer(draw, x, y, size, color):
    stem_x = x + size / 2
    bulb_radius = 2

    draw.line((stem_x, y, stem_x, y + size - bulb_radius), fill=color, width=1)
    draw.ellipse(
        (stem_x - bulb_radius, y + size - bulb_radius * 2, stem_x + bulb_radius, y + size),
        fill=color,
    )

def draw_thermometer_warning(draw, x, y, color, width=6, height=18):
    """Draw a compact thermometer icon."""
    bulb_radius = 3
    stem_width = 2

    bulb_center_x = x + width // 2
    bulb_center_y = y + height - bulb_radius

    # Thermometer stem
    stem_left = bulb_center_x - stem_width // 2
    stem_top = y + 2
    stem_bottom = bulb_center_y

    draw.rounded_rectangle(
        (
            stem_left,
            stem_top,
            stem_left + stem_width,
            stem_bottom,
        ),
        radius=stem_width // 2,
        fill=color,
    )

    # Thermometer bulb
    draw.ellipse(
        (
            bulb_center_x - bulb_radius,
            bulb_center_y - bulb_radius,
            bulb_center_x + bulb_radius,
            bulb_center_y + bulb_radius,
        ),
        fill=color,
    )


def draw_icon_percent(draw, x, y, size, color):
    draw.line((x, y + size, x + size, y), fill=color, width=1)
    draw.ellipse((x, y, x + 2, y + 2), outline=color)
    draw.ellipse((x + size - 2, y + size - 2, x + size, y + size), outline=color)


# -----------------------------
# Network Status icons
# -----------------------------

def draw_wireless_icon(draw, x, y, size, color):
    """RSS/wifi-style icon: a dot at the bottom-left corner with two bold
    quarter-arcs sweeping toward the upper-right, anchored at (x, y) as the
    icon's bottom-left corner. Used to show a background sync (e.g. a Home
    Assistant fetch) is in progress."""
    cx = x
    cy = y + size

    dot_radius = max(1, round(size * 0.12))
    draw.ellipse(
        (cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius),
        fill=color,
    )

    stroke_width = 1

    for radius in (size * 0.35, size * 0.70):
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
        draw.arc(bbox, start=260, end=370, fill=color, width=stroke_width)

# FIN