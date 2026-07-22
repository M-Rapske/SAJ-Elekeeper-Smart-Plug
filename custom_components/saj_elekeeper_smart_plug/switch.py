"""Switch entities for SAJ Elekeeper Smart Plugs."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ElekeeperDataUpdateCoordinator
from .models import SmartPlugInfo

SMART_PLUG_SWITCH_DESCRIPTION = SwitchEntityDescription(
    key="smart_plug",
    translation_key="smart_plug",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one controllable switch for every discovered Smart Plug."""
    coordinator: ElekeeperDataUpdateCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        ElekeeperSmartPlugSwitch(coordinator, plug.serial)
        for plug in coordinator.data
    )


class ElekeeperSmartPlugSwitch(
    CoordinatorEntity[ElekeeperDataUpdateCoordinator], SwitchEntity
):
    """Control a Smart Plug through the Elekeeper cloud."""

    _attr_has_entity_name = True
    entity_description = SMART_PLUG_SWITCH_DESCRIPTION

    def __init__(
        self, coordinator: ElekeeperDataUpdateCoordinator, serial: str
    ) -> None:
        """Initialize a Smart Plug switch."""
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"smart_plug_{serial}_switch"

    def _plug(self) -> SmartPlugInfo | None:
        """Return the latest dedicated Smart Plug telemetry row."""
        return next(
            (
                plug
                for plug in self.coordinator.data
                if plug.serial == self._serial
            ),
            None,
        )

    @property
    def available(self) -> bool:
        """Mark a Smart Plug unavailable when Elekeeper stops reporting it."""
        return super().available and self._plug() is not None

    @property
    def is_on(self) -> bool | None:
        """Return the switch state supplied by Elekeeper."""
        plug = self._plug()
        return plug.is_on if plug else None

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the Smart Plug on."""
        await self.coordinator.async_set_smart_plug_state(self._serial, True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the Smart Plug off."""
        await self.coordinator.async_set_smart_plug_state(self._serial, False)

    @property
    def device_info(self) -> DeviceInfo:
        """Register the switch under the same Smart Plug device as its sensors."""
        plug = self._plug()
        model = plug.model if plug and plug.model else "Smart Plug"
        name = plug.name if plug and plug.name else f"{model} {self._serial[-6:]}"
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=name,
            manufacturer="SAJ",
            model=model,
            serial_number=self._serial,
        )
