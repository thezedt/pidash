#!/usr/bin/env python3
"""Client helpers for talking to the Home Assistant REST API."""

import requests

import config


def get_state(entity_id):

    url = f"{config.HA_URL.rstrip('/')}/api/states/{entity_id}"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {config.HA_TOKEN}",
            "Content-Type": "application/json",
        },
        timeout=5,
    )
    response.raise_for_status()

    data = response.json()

    try:
        return float(data["state"])
    except (ValueError, TypeError):
        return None


def read_values():
    values = {}

    for name, entity_id in config.SENSORS.items():
        try:
            values[name] = get_state(entity_id)
        except requests.RequestException:
            values[name] = None

    return values
