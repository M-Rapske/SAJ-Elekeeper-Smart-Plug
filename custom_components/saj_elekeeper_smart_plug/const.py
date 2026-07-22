"""Constants for the SAJ Elekeeper Smart Plug integration."""

from datetime import timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN = "saj_elekeeper_smart_plug"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

CONF_PLANT_UID = "plant_uid"
CONF_PLANT_NAME = "plant_name"
CONF_REGION = "region"
CONF_LEGACY_SCAN_INTERVAL = "scan_interval"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

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

DEFAULT_SCAN_INTERVAL_MINUTES: Final = 1
MIN_SCAN_INTERVAL_MINUTES: Final = 1
MAX_SCAN_INTERVAL_MINUTES: Final = 1440
DEFAULT_SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
