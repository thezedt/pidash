#!/usr/bin/env python3
"""Entry point: polls Home Assistant, handles buttons, and renders it on the LCD."""

import time

import dash_setup
import dash_functions

import traceback


def compute_brightness():
    # lower brightness between 23:30 and 07:30
    now = time.localtime()
    minutes = now.tm_hour * 60 + now.tm_min

    # Quiet period: 23:30 through 07:30
    if minutes >= 23 * 60 + 30 or minutes < 7 * 60 + 30:
        return 25
    return 100


def main():
    backlight_pwm = dash_setup.setup_backlight()
    dash_setup.setup_buttons()
    lcd = dash_setup.setup_lcd()

    state = dash_functions.DashboardState()
    values = {}
    last_sensor_poll = 0.0

    try:
        while True:
            try:
                for button in dash_functions.read_button_events():
                    state.handle_event(button)

                state.check_idle()

                now = time.monotonic()
                if now - last_sensor_poll >= dash_setup.UPDATE_SECONDS:
                    backlight_pwm.set_PWM_dutycycle(
                        dash_setup.BACKLIGHT_PIN, compute_brightness()
                    )
                    values = dash_functions.read_values()
                    last_sensor_poll = now

                dash_functions.render(lcd, state, values)

                time.sleep(dash_setup.BUTTON_POLL_SECONDS)

            except Exception as error:
                dash_functions.draw_error(lcd, error)
                print("Dashboard crashed:")
                traceback.print_exc()

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        print("Running cleanup")

        if backlight_pwm is not None and backlight_pwm.connected:
            backlight_pwm.set_PWM_dutycycle(dash_setup.BACKLIGHT_PIN, 0)
            backlight_pwm.stop()


if __name__ == "__main__":
    main()
