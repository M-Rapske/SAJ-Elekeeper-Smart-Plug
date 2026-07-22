"""SAJ Elekeeper Smart Plug integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PLANT_NAME, CONF_PLANT_UID, PLATFORMS
from .coordinator import ElekeeperDataUpdateCoordinator


@dataclass
class ElekeeperRuntimeData:
    """Runtime objects owned by one Elekeeper config entry."""

    coordinator: ElekeeperDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SAJ Elekeeper Smart Plug from a config entry."""
    old_default_titles = {
        entry.data.get(CONF_PLANT_NAME),
        entry.data.get(CONF_PLANT_UID),
    }
    if entry.title in old_default_titles:
        plant_name = entry.data.get(CONF_PLANT_NAME, entry.data[CONF_PLANT_UID])
        hass.config_entries.async_update_entry(
            entry,
            title=f"SAJ Elekeeper Smart Plug ({plant_name})",
        )

    coordinator = ElekeeperDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = ElekeeperRuntimeData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a SAJ Elekeeper Smart Plug config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.coordinator.async_close()
    return unloaded
