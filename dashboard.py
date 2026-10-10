#!/usr/bin/env python3
"""Entry point: polls Home Assistant and renders it on the LCD."""

import time

import dash_setup
import dash_functions

import traceback


def main():
    backlight_pwm = dash_setup.setup_backlight()
    lcd = dash_setup.setup_lcd()

    try:
        while True:
            try:
                # lower brightness between 23:30 and 07:30
                now = time.localtime()
                minutes = now.tm_hour * 60 + now.tm_min

                # Quiet period: 23:30 through 07:30
                if minutes >= 23 * 60 + 30 or minutes < 7 * 60 + 30:
                    brightness = 25
                else:
                    brightness = 100

                backlight_pwm.set_PWM_dutycycle(dash_setup.BACKLIGHT_PIN, brightness)

                values = dash_functions.read_values()
                dash_functions.draw_dashboard(lcd, values)
                
                time.sleep(dash_setup.UPDATE_SECONDS)

            except Exception as error:
                dash_functions.draw_error(lcd, error)
                print("Dashboard crashed:")
                traceback.print_exc()

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        print("Running cleanup")

        if backlight_pwm is not None and backlight_pwm.connected:
            backlight_pwm.set_PWM_dutycycle( dash_setup.BACKLIGHT_PIN, 0 )
            backlight_pwm.stop()


if __name__ == "__main__":
    main()
