#!/usr/bin/env python3
"""Shared color palette and small color-selection helpers.

`active_color` and `over_limit_color` replace the repeated
"if value crosses some threshold, use color A else color B" blocks that
showed up for every reading (solar / grid / house / battery).
"""

BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
GREY = (80, 80, 80)
IDLE_COLOR = (120, 120, 120)

SOLAR_IDLE_COLOR = IDLE_COLOR
SOLAR_ACTIVE_COLOR = (255, 210, 0)  # bright yellow

EXPORT_COLOR = (80, 100, 150)
BATTERY_COLOR = (115, 70, 105)
HOUSE_COLOR = (35, 35, 35)

GREEN = (75, 135, 120)
RED = (200, 20, 20)


def active_color(value, threshold, active, idle=IDLE_COLOR, strict=False):
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


def over_limit_color(value, limit, over_color=RED, default_color=WHITE):
    """Return `over_color` if value is at/above `limit`, else `default_color`."""
    if value is not None and value >= limit:
        return over_color
    return default_color
