#!/usr/bin/env python3
"""Color-selection helpers, text formatting, and icon/arrow drawing primitives."""

import dash_setup

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
    return default_color


# -----------------------------
# Formatting helpers
# -----------------------------

def volts(value):
    if value is None:
        return "--"

    return f"{value:.1f} V"

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
        return "   \u221e"

    try:
        total_minutes = int(float(minutes))
    except (ValueError, TypeError):
        return "   X"

    if total_minutes < 0:
        total_minutes = 0

    hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    return f"{hours}h {remaining_minutes:02d}m"


def text_center(draw, xy, text, fill, font):
    width = draw.textbbox((0, 0), text, font=font)[2]
    draw.text((xy[0] - width / 2, xy[1]), text, fill=fill, font=font)


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


def draw_icon_percent(draw, x, y, size, color):
    draw.line((x, y + size, x + size, y), fill=color, width=1)
    draw.ellipse((x, y, x + 2, y + 2), outline=color)
    draw.ellipse((x + size - 2, y + size - 2, x + size, y + size), outline=color)
