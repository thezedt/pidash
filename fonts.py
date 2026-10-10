#!/usr/bin/env python3
"""Font loading for the dashboard display."""

### needs package fonts-dejavu-core ###

from PIL import ImageFont

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
