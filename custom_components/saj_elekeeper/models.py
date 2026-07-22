"""Models for Elekeeper data not supplied by the client library."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _as_float(value: Any) -> float | None:
    """Return a numeric API value as a float, or ``None`` when absent."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    """Convert Elekeeper's integer/string switch fields to a boolean."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = value.casefold()
        if value in {"on", "true", "1"}:
            return True
        if value in {"off", "false", "0"}:
            return False
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class SmartPlugInfo:
    """Telemetry reported by Elekeeper's Smart Socket device list."""

    serial: str
    name: str | None = None
    model: str | None = None
    status: str | None = None
    is_on: bool | None = None
    power_w: float | None = None
    today_energy_kwh: float | None = None
    month_energy_kwh: float | None = None
    total_energy_kwh: float | None = None
    voltage_v: float | None = None
    current_a: float | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SmartPlugInfo | None:
        """Create a model for a Smart Socket (Elekeeper type ``1``) only."""
        if str(data.get("smartDeviceType")) != "1":
            return None

        serial = data.get("deviceSn")
        if not serial:
            return None

        return cls(
            serial=str(serial),
            name=data.get("deviceName") or None,
            model=data.get("smartDeviceTypeName") or "Smart Plug",
            status=(
                data.get("onlineStatusName")
                or data.get("deviceStatusName")
                or data.get("deviceStatus")
                or None
            ),
            is_on=_as_bool(
                data["deviceSwitch"]
                if data.get("deviceSwitch") is not None
                else data.get("deviceState")
            ),
            power_w=_as_float(data.get("power")),
            today_energy_kwh=_as_float(data.get("todayEnergy")),
            month_energy_kwh=_as_float(data.get("monthEnergy")),
            total_energy_kwh=_as_float(data.get("totalEnergy")),
            voltage_v=_as_float(data.get("voltage")),
            current_a=_as_float(data.get("current")),
            raw=data,
        )
