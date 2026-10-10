#!/usr/bin/env python3
"""Hardware setup: backlight GPIO and the LCD device."""

import RPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.lcd.device import st7735

import config


def setup_backlight():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(config.BACKLIGHT_PIN, GPIO.OUT, initial=GPIO.HIGH)


def setup_lcd():
    # Waveshare 1.44-inch LCD HAT, model 13891
    return st7735(
        spi(
            port=config.LCD_SPI_PORT,
            device=config.LCD_SPI_DEVICE,
            gpio_DC=config.LCD_GPIO_DC,
            gpio_RST=config.LCD_GPIO_RST,
        ),
        width=config.LCD_WIDTH,
        height=config.LCD_HEIGHT,
        rotate=config.LCD_ROTATE,
        h_offset=config.LCD_H_OFFSET,
        v_offset=config.LCD_V_OFFSET,
        bgr=config.LCD_BGR,
    )
