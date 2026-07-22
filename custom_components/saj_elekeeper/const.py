"""Constants for the SAJ Elekeeper Smart Plug integration."""

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN = "saj_elekeeper"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

CONF_PLANT_UID = "plant_uid"
CONF_PLANT_NAME = "plant_name"
CONF_REGION = "region"
CONF_SCAN_INTERVAL = "scan_interval"

REGION_EUROPE: Final = "europe"
REGION_CHINA: Final = "china"
REGION_OTHER: Final = "other"
DEFAULT_REGION: Final = REGION_EUROPE

REGION_BASE_URLS: Final[dict[str, str]] = {
    REGION_EUROPE: "https://eop.saj-electric.com",
    REGION_CHINA: "https://op.saj-electric.cn",
    REGION_OTHER: "https://iop.saj-electric.com",
}
REGION_OPTIONS: Final[dict[str, str]] = {
    REGION_EUROPE: "Europe (eop.saj-electric.com)",
    REGION_CHINA: "China (op.saj-electric.cn)",
    REGION_OTHER: "Other countries / regions (iop.saj-electric.com)",
}

DEFAULT_SCAN_INTERVAL_SECONDS: Final = 60
POLL_INTERVAL_OPTIONS: Final[dict[int, str]] = {
    10: "10 seconds",
    15: "15 seconds",
    30: "30 seconds",
    60: "1 minute",
    120: "2 minutes",
    300: "5 minutes",
}
DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
