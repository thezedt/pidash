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
    lcd = dash_setup.setup_lcd()

    try:
        # Do not initialize buttons or contact Home Assistant until the
        # Pi has an IPv4 address in the required network range.
        while not dash_functions.is_on_required_network():
            dash_functions.draw_network_error(lcd)
            time.sleep(2)

        dash_setup.setup_buttons()
        state = dash_functions.DashboardState()
        last_sensor_poll = 0.0
        last_signature = None

        # One-time blocking read so there's data to show immediately; every
        # refresh after this happens on a background thread (see
        # dash_functions.request_values_refresh) so it never blocks buttons.
        dash_functions.set_latest_values(dash_functions.read_values())
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
                    dash_functions.request_values_refresh()
                    last_sensor_poll = now

                # Buttons are still polled every BUTTON_POLL_SECONDS for
                # responsiveness, but the (expensive) actual redraw + SPI
                # transfer only needs to happen when something that
                # affects the image has actually changed.
                signature = (
                    state.mode,
                    state.active_screen,
                    state.menu_selected,
                    getattr(state, "pending_action_label", None),
                    dash_functions.is_fetching(),
                    dash_functions.is_ha_reachable(),
                    dash_functions.get_values_version(),
                )

                if signature != last_signature:
                    values = dash_functions.get_latest_values()
                    dash_functions.render(lcd, state, values)
                    last_signature = signature

                time.sleep(dash_setup.BUTTON_POLL_SECONDS)

            except Exception as error:
                dash_functions.draw_error(lcd, error)
                print("Dashboard crashed:")
                traceback.print_exc()
                last_signature = None  # force a redraw next tick

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        print("Running cleanup")

        if backlight_pwm is not None and backlight_pwm.connected:
            backlight_pwm.set_PWM_dutycycle(dash_setup.BACKLIGHT_PIN, 0)
            backlight_pwm.stop()


if __name__ == "__main__":
    main()

# FIN