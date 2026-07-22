"""Diagnostics for SAJ Elekeeper Smart Plug without sensitive data."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_REGION, DEFAULT_REGION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return a compact, non-sensitive runtime summary."""
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": {
            "username_configured": bool(entry.data.get(CONF_USERNAME)),
            "region": entry.data.get(CONF_REGION, DEFAULT_REGION),
            "plant_uid": entry.data.get("plant_uid"),
            "plant_name": entry.data.get("plant_name"),
        },
        "smart_plugs": {
            "smart_plug_count": len(coordinator.data),
            "smart_plug_api_response_count": coordinator.smart_plug_api_response_count,
            "smart_plug_api_error": coordinator.smart_plug_api_error,
        },
    }
