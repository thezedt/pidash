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
