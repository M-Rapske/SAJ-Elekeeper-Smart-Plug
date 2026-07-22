"""Sensor entities for SAJ Elekeeper Smart Plug."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ElekeeperDataUpdateCoordinator
from .models import SmartPlugInfo

SMART_PLUG_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_w",
        translation_key="smart_plug_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    SensorEntityDescription(
        key="total_energy_kwh",
        translation_key="smart_plug_total_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="today_energy_kwh",
        translation_key="smart_plug_today_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="month_energy_kwh",
        translation_key="smart_plug_month_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="voltage_v",
        translation_key="smart_plug_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="current_a",
        translation_key="smart_plug_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(key="status", translation_key="smart_plug_status"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Plug sensors for one configured Elekeeper plant."""
    coordinator: ElekeeperDataUpdateCoordinator = entry.runtime_data.coordinator
    async_add_entities(
        ElekeeperSmartPlugSensor(coordinator, plug.serial, description)
        for plug in coordinator.data
        for description in SMART_PLUG_SENSOR_DESCRIPTIONS
    )


class ElekeeperSmartPlugSensor(
    CoordinatorEntity[ElekeeperDataUpdateCoordinator], SensorEntity
):
    """Represent one metric of an Elekeeper Smart Plug."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElekeeperDataUpdateCoordinator,
        serial: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a Smart Plug sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._serial = serial
        self._attr_unique_id = f"smart_plug_{serial}_{description.key}"

    def _plug(self) -> SmartPlugInfo | None:
        """Return the latest telemetry row for this Smart Plug."""
        return next(
            (plug for plug in self.coordinator.data if plug.serial == self._serial),
            None,
        )

    @property
    def available(self) -> bool:
        """Mark a removed Smart Plug unavailable."""
        return super().available and self._plug() is not None

    @property
    def native_value(self) -> str | float | None:
        """Return the selected Smart Plug telemetry value."""
        plug = self._plug()
        return getattr(plug, self.entity_description.key) if plug else None

    @property
    def device_info(self) -> DeviceInfo:
        """Register the sensor with its physical Smart Plug device."""
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
