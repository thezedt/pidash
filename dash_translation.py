#!/usr/bin/env python3
"""Translation strings for PiDash."""

# Default language
CURRENT_LANGUAGE = "ro"

LANGUAGES = {
    "en": {
        # Menu
        "menu_back": "« Exit",
        "menu_solar": "Solar",
        "menu_temps": "Temperatures",
        "menu_params": "Parameters",
        "menu_ev": "EV",
        "menu_energy": "Energy",
        "menu_advanced": "Advanced »",

        # Submenu
        "submenu_back": "« Back",
        "submenu_restart_network": "Restart Network",
        "submenu_brightness": "Brightness: {}%",
        "submenu_interval": "Refresh: {}s",
        "submenu_rotation": "Rotation: {}°",
        "submenu_language": "Language: {}",
        "submenu_restart_pidash": "Restart PiDash",
        "submenu_test_mode": "Test Mode",
        "submenu_restart_pi": "Restart Pi",
        "submenu_shutdown_pi": "Shutdown Pi",

        # Screen Titles
        "screen_solar": "Solar",
        "screen_temps": "Temperatures",
        "screen_params": "Parameters",
        "screen_ev": "EV",
        "screen_energy": "Energy",

        # Labels
        "label_error": "Error \u26A0",
        "label_ha_error": "HA Error",
        "label_network_error": "Network Error",
        "label_pi_dash": "Pi Dash",
        "label_confirm": "{}?",
        "label_restarting": "Restarting...",
        "label_connected": "{} / {}",

        # Temps screen labels
        "temp_outside": "Outside",
        "temp_outside_humidity": "Out. Hum.",
        "temp_pantry": "Pantry",
        "temp_pantry_humidity": "Pantry Hum.",
        "temp_hallway": "Hallway",
        "temp_outside2": "Garden",
        "temp_attic": "Attic",
        "temp_bicaz": "Bicaz",

        # Params screen labels
        "params_inverter_temp": "Inv. Temp",
        "params_bms_temp": "BMS Temp",
        "params_battery_temp": "Batt. Temp",
        "params_pi_temp": "Pi Temp",
        "params_inverter_limit": "Inv. Limit",
        "params_battery_limit": "Batt. Limit",
        "params_charge_power": "Charge Pwr.",
        "params_discharge_power": "Disch. Pwr.",

        # EV screen
        "ev_battery": "Battery",
        "ev_charge_power": "Charge Pwr.",
        "ev_charge_current": "Charge Curr.",
        "ev_autonomy": "Autonomy",
        "ev_charge_status": "Status",
        "ev_charging": "Charging",
        "ev_kwh_to_limit": "kWh Left",
        "ev_time_to_limit": "Time Left",
        "ev_temp": "Temp.",

        # Units
        "unit_volts": "V",
        "unit_watts": "W",
        "unit_kw": "kW",
        "unit_kwh": "kWh",
        "unit_percent": "%",
        "unit_degrees": "°C",
        "unit_amps": "A",
        "unit_hours": "h",
        "unit_minutes": "m",
        "unit_km": "km",

        # Network
        "network_restart_label": "Restart network...",
        "network_connected": "{} / {}",
        "network_disconnected": "Disconnected",
        "network_ip_address": "IP Address: {}",
        "network_ssid": "SSID: {}",

        # Confirmation
        "confirm_restart_pi": "Restart Pi",
        "confirm_shutdown_pi": "Shutdown Pi",

        # Misc
        "loading": "Loading...",
        "unknown_network": "Unknown network",
        "cannot_reach_ha": "Cannot reach Home Assistant",
    },
    "ro": {
        # Menu
        "menu_back": "« Ieşire",
        "menu_solar": "Solar",
        "menu_temps": "Temperaturi",
        "menu_params": "Parametri",
        "menu_ev": "Spring",
        "menu_energy": "Energie",
        "menu_advanced": "Avansat »",

        # Submenu
        "submenu_back": "« Înapoi",
        "submenu_restart_network": "Repornire reţea",
        "submenu_brightness": "Luminozitate: {}%",
        "submenu_interval": "Interval: {}s",
        "submenu_rotation": "Rotire ecran: {}°",
        "submenu_language": "Limba: {}",
        "submenu_restart_pidash": "Repornire PiDash",
        "submenu_test_mode": "Mod test",
        "submenu_restart_pi": "Repornire Pi",
        "submenu_shutdown_pi": "Oprire Pi",

        # Screen Titles
        "screen_solar": "Solar",
        "screen_temps": "Temperaturi",
        "screen_params": "Parametri",
        "screen_ev": "Spring",
        "screen_energy": "Energie",

        # Labels
        "label_error": "Eroare \u26A0",
        "label_ha_error": "Eroare HA",
        "label_network_error": "Eroare reţea",
        "label_pi_dash": "Pi Dash",
        "label_confirm": "{}?",
        "label_restarting": "Repornire...",
        "label_connected": "{} / {}",

        # Temps screen labels
        "temp_outside": "Afară",
        "temp_outside_humidity": "Um. Afară",
        "temp_pantry": "Cămară",
        "temp_pantry_humidity": "Um. Cămară",
        "temp_hallway": "Hol",
        "temp_outside2": "Grădină",
        "temp_attic": "Pod",
        "temp_bicaz": "Bicaz",

        # Params screen labels
        "params_inverter_temp": "Temp. Inv.",
        "params_bms_temp": "Temp. BMS",
        "params_battery_temp": "Temp. Bat.",
        "params_pi_temp": "Temp. PI",
        "params_inverter_limit": "Limită Inv.",
        "params_battery_limit": "Limită Bat.",
        "params_charge_power": "Încărc. Bat.",
        "params_discharge_power": "Desc. Bat.",

        # EV screen
        "ev_battery": "Baterie",
        "ev_charge_power": "Putere Înc.",
        "ev_charge_current": "Curent Înc.",
        "ev_autonomy": "Autonomie",
        "ev_charge_status": "Stare",
        "ev_charging": "Încărcare",
        "ev_kwh_to_limit": "KWh de înc.",
        "ev_time_to_limit": "Timp Înc.",
        "ev_temp": "Temperatură",

        # Units
        "unit_volts": "V",
        "unit_watts": "W",
        "unit_kw": "kW",
        "unit_kwh": "kWh",
        "unit_percent": "%",
        "unit_degrees": "°C",
        "unit_amps": "A",
        "unit_hours": "h",
        "unit_minutes": "m",
        "unit_km": "km",

        # Network
        "network_restart_label": "Repornire rețea...",
        "network_connected": "{} / {}",
        "network_disconnected": "Neconectat",
        "network_ip_address": "Adresă IP: {}",
        "network_ssid": "SSID: {}",

        # Confirmation
        "confirm_restart_pi": "Repornire Pi",
        "confirm_shutdown_pi": "Oprire Pi",

        # Misc
        "loading": "Se încarca...",
        "unknown_network": "Reţea necunoscută",
        "cannot_reach_ha": "Conexiune la HA imposibilă",
    }
}

def get_text(key, *args):
    """Get localized text for a key, with optional formatting."""
    lang = LANGUAGES.get(CURRENT_LANGUAGE, LANGUAGES["en"])
    text = lang.get(key, key)
    if args:
        return text.format(*args)
    return text

def set_language(lang_code):
    """Set the current language for the current session only."""
    global CURRENT_LANGUAGE
    if lang_code in LANGUAGES:
        CURRENT_LANGUAGE = lang_code

# FIN