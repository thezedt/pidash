#!/usr/bin/env python3
"""Text formatting helpers shared by the dashboard display."""


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
