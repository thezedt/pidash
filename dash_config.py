#!/usr/bin/env python3
"""Home Assistant API credentials.

Keep this file out of version control if you hardcode a real HA_TOKEN here -
prefer setting HA_URL / HA_TOKEN as environment variables instead.
"""

import os
import ipaddress

HA_URL = os.getenv("HA_URL", "http://REDACTED:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "REDACTED")

# Expected IP address range for correct functionality
REQUIRED_NETWORK = ipaddress.ip_network("192.168.1.0/24")

# FIN