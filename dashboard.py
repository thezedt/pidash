#!/usr/bin/env python3
"""Entry point: polls Home Assistant and renders it on the LCD."""

import time

import config
import display
import hardware
from ha_client import read_values


def main():
    hardware.setup_backlight()
    lcd = hardware.setup_lcd()

    while True:
        try:
            values = read_values()
            display.draw_dashboard(lcd, values)
        except Exception as error:
            display.draw_error(lcd, error)

        time.sleep(config.UPDATE_SECONDS)


if __name__ == "__main__":
    main()
