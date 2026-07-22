"""Data coordinator for SAJ Elekeeper."""

from __future__ import annotations

from dataclasses import replace
import logging
from time import monotonic
from typing import Final

import httpx
from elekeeper import SajApiError, SajAuthError, SajClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import async_create_client, async_post_v2
from .const import (
    CONF_PLANT_UID,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    DEFAULT_REGION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
)
from .models import SmartPlugInfo

_LOGGER = logging.getLogger(__name__)
_AUTH_STATUS_CODES: Final = {401, 403}
_SMART_DEVICE_LIST_PATH: Final = "/api/v2/monitor/plantDevice/listSmartDeviceForWeb"
_SMART_PLUG_DETAIL_PATH: Final = "/api/v2/monitor/device/querySmartDeviceDetail"
_SMART_PLUG_SWITCH_PATH: Final = "/api/v2/remote/ems/setSwitch"
_PENDING_SWITCH_STATE_SECONDS: Final = 15


class ElekeeperDataUpdateCoordinator(DataUpdateCoordinator[list[SmartPlugInfo]]):
    """Fetch Smart Plug data for one Elekeeper plant."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator without contacting the cloud."""
        try:
            scan_interval = timedelta(
                seconds=int(
                    entry.options.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL_SECONDS,
                    )
                )
            )
        except (TypeError, ValueError):
            scan_interval = DEFAULT_SCAN_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=scan_interval,
            always_update=False,
        )
        self.config_entry = entry
        self._client: SajClient | None = None
        self.smart_plug_api_error: str | None = None
        self.smart_plug_api_response_count: int | None = None
        self._org_code: str | None = None
        self._pending_switch_states: dict[str, tuple[bool, float]] = {}

    async def _async_setup(self) -> None:
        """Authenticate once before the initial data refresh."""
        self._client = await async_create_client(
            self.hass,
            region=self.config_entry.data.get(CONF_REGION, DEFAULT_REGION),
        )
        await self._async_authenticate()

    async def _async_authenticate(self) -> None:
        """Authenticate without ever logging credentials."""
        if self._client is None:
            self._client = await async_create_client(
                self.hass,
                region=self.config_entry.data.get(CONF_REGION, DEFAULT_REGION),
            )
        try:
            await self._client.authenticate(
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_PASSWORD],
            )
        except (SajAuthError, SajApiError) as err:
            raise ConfigEntryAuthFailed("Elekeeper rejected the credentials") from err
        except httpx.HTTPError as err:
            raise UpdateFailed(f"Unable to authenticate with Elekeeper: {err}") from err

    async def _async_update_data(self) -> list[SmartPlugInfo]:
        """Request Smart Plug data, retrying once after token expiry."""
        try:
            return await self._async_fetch_data()
        except SajAuthError as err:
            raise ConfigEntryAuthFailed("Elekeeper authentication expired") from err
        except httpx.HTTPStatusError as err:
            if err.response.status_code not in _AUTH_STATUS_CODES:
                message = f"Error communicating with Elekeeper: {err}"
                raise UpdateFailed(message) from err
        except (SajApiError, httpx.HTTPError) as err:
            raise UpdateFailed(f"Error communicating with Elekeeper: {err}") from err

        # The portal can invalidate a bearer token independently of its refresh
        # lifetime. Re-login once; a wrong password is surfaced as reauth.
        await self._async_authenticate()
        try:
            return await self._async_fetch_data()
        except SajAuthError as err:
            raise ConfigEntryAuthFailed("Elekeeper authentication expired") from err
        except (SajApiError, httpx.HTTPError) as err:
            raise UpdateFailed(f"Error communicating with Elekeeper: {err}") from err

    async def _async_fetch_data(self) -> list[SmartPlugInfo]:
        """Fetch the Smart Plug list and its detailed telemetry."""
        if self._client is None:
            raise RuntimeError("Elekeeper client was not initialized")
        plant_uid = self.config_entry.data[CONF_PLANT_UID]
        login_info = await self._client.get_login_info()
        org_code_value = login_info.raw.get("orgCode")
        org_code = org_code_value if isinstance(org_code_value, str) else None
        self._org_code = org_code
        return await self._async_fetch_smart_plugs(plant_uid, org_code=org_code)

    async def async_set_smart_plug_state(self, serial: str, is_on: bool) -> None:
        """Set a Smart Plug state through Elekeeper's V2 remote endpoint."""
        if self._client is None:
            raise HomeAssistantError("Elekeeper client was not initialized")

        try:
            await async_post_v2(
                self._client,
                _SMART_PLUG_SWITCH_PATH,
                {"deviceSn": serial, "onOff": 1 if is_on else 0},
                org_code=self._org_code,
            )
        except SajAuthError as err:
            raise ConfigEntryAuthFailed("Elekeeper authentication expired") from err
        except (SajApiError, httpx.HTTPError) as err:
            raise HomeAssistantError(
                f"Unable to change Smart Plug {serial} state: {err}"
            ) from err

        self._pending_switch_states[serial] = (
            is_on,
            monotonic() + _PENDING_SWITCH_STATE_SECONDS,
        )
        self.async_set_updated_data(
            [
                replace(plug, is_on=is_on) if plug.serial == serial else plug
                for plug in self.data
            ]
        )
        await self.async_request_refresh()

    async def _async_fetch_smart_plugs(
        self, plant_uid: str, *, org_code: str | None
    ) -> list[SmartPlugInfo]:
        """Fetch Smart Plug list and enrich it with the detail endpoint."""
        if self._client is None:
            raise RuntimeError("Elekeeper client was not initialized")
        try:
            response = await async_post_v2(
                self._client,
                _SMART_DEVICE_LIST_PATH,
                {"plantUid": plant_uid},
                org_code=org_code,
            )
        except (SajApiError, httpx.HTTPError) as err:
            self.smart_plug_api_error = str(err)
            self.smart_plug_api_response_count = None
            raise UpdateFailed(
                f"Unable to refresh Elekeeper Smart Plug data: {err}"
            ) from err

        devices = response.get("smartDeviceList")
        if not isinstance(devices, list):
            self.smart_plug_api_error = "Response did not contain smartDeviceList"
            self.smart_plug_api_response_count = None
            raise UpdateFailed("Elekeeper returned no Smart Plug device list")

        self.smart_plug_api_error = None
        self.smart_plug_api_response_count = len(devices)

        smart_plugs: list[SmartPlugInfo] = []
        for device in devices:
            if not isinstance(device, dict):
                continue
            plug = SmartPlugInfo.from_dict(device)
            if plug is None:
                continue

            # The list contains instant power and total energy. The detail
            # endpoint supplies the daily/monthly counters, voltage and current.
            try:
                detail = await async_post_v2(
                    self._client,
                    _SMART_PLUG_DETAIL_PATH,
                    {"plantUid": plant_uid, "deviceSn": plug.serial},
                    org_code=org_code,
                )
            except (SajApiError, httpx.HTTPError) as err:
                _LOGGER.debug(
                    "Unable to refresh Elekeeper Smart Plug detail for %s: %s",
                    plug.serial,
                    err,
                )
            else:
                if isinstance(detail, dict):
                    detail_fields = {
                        key: value for key, value in detail.items() if value is not None
                    }
                    plug = SmartPlugInfo.from_dict({**device, **detail_fields}) or plug
            smart_plugs.append(self._apply_pending_switch_state(plug))

        return smart_plugs

    def _apply_pending_switch_state(self, plug: SmartPlugInfo) -> SmartPlugInfo:
        """Avoid reverting a switch while the cloud applies a confirmed command."""
        pending = self._pending_switch_states.get(plug.serial)
        if pending is None:
            return plug

        requested_state, expires_at = pending
        if plug.is_on == requested_state or monotonic() >= expires_at:
            self._pending_switch_states.pop(plug.serial, None)
            return plug
        return replace(plug, is_on=requested_state)

    async def async_close(self) -> None:
        """Close the underlying HTTP client when the config entry unloads."""
        if self._client is not None:
            await self._client.aclose()
