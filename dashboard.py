#!/usr/bin/env python3
"""Entry point: polls Home Assistant, handles buttons, and renders it on the LCD."""

import time

import dash_setup
import dash_functions
import dash_translation

import traceback


def main():
    backlight_pwm = dash_setup.setup_backlight()
    dash_functions.set_backlight_pwm(backlight_pwm)
    lcd = dash_setup.setup_lcd()
    dash_translation.CURRENT_LANGUAGE = dash_setup.DEFAULT_LANGUAGE

    try:
        # Do not initialize buttons or contact Home Assistant until the
        # Pi has an IPv4 address in the required network range.
        while not dash_functions.is_on_required_network():
            dash_functions.draw_network_error(lcd)
            time.sleep(2)

        dash_setup.setup_buttons()
        state = dash_functions.DashboardState()
        dash_functions.set_current_rotation(dash_setup.SCREEN_ROTATION)
        last_sensor_poll = 0.0
        last_signature = None

        # One-time blocking read so there's data to show immediately; every
        # refresh after this happens on a background thread (see
        # dash_functions.request_values_refresh) so it never blocks buttons.
        dash_functions.set_latest_values(dash_functions.read_values())
        while True:
            try:
                # Force redraw if language changed
                if hasattr(state, '_language_changed') and state._language_changed:
                    last_signature = None
                    state._language_changed = False

                for button in dash_functions.read_button_events():
                    state.handle_event(button)

                state.check_idle()

                now = time.monotonic()
                if now - last_sensor_poll >= dash_setup.UPDATE_SECONDS:
                    backlight_pwm.set_PWM_dutycycle(
                        dash_setup.BACKLIGHT_PIN, dash_functions.compute_brightness()
                    )
                    dash_functions.request_values_refresh()
                    last_sensor_poll = now

                # Menu/submenu/confirm screens show live-updating content
                # (a setting being adjusted, network-restart status, the
                # test-mode clock) that isn't reflected in the signature
                # below, so always redraw while one of them is visible.
                # The sensor screens still use the change-gated signature,
                # since that's where the CPU savings actually matter.
                if state.mode in ("menu", "submenu", "confirm"):
                    values = dash_functions.get_latest_values()
                    dash_functions.render(lcd, state, values)
                    last_signature = None  # force a fresh check on return to a screen
                else:
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