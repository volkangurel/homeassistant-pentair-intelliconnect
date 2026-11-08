"""Service actions package for pentair_pool."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol

from custom_components.pentair_pool.const import DOMAIN, LOGGER
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall


SERVICE_RELOAD_DATA = "reload_data"
SERVICE_SET_FIELDS = "set_fields"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration-level services.

    `pentair_pool.reload_data` forces a coordinator refresh for every
    configured account, which is useful after manually changing settings
    on a controller.
    """

    async def handle_reload_data(_call: ServiceCall) -> None:
        for entry in hass.config_entries.async_entries(DOMAIN):
            coordinator = entry.runtime_data.coordinator if hasattr(entry, "runtime_data") else None
            if coordinator is not None:
                await coordinator.async_request_refresh()

    async def handle_set_fields(call: ServiceCall) -> None:
        """Advanced: write raw Pentair cloud fields (e.g. {"ifd3": "1"}).

        `device` is the Pentair device id; when omitted, the first device
        that already reports every requested field is used.
        """
        fields = {str(k): str(v) for k, v in dict(call.data["fields"]).items()}
        if not fields:
            raise ServiceValidationError("fields must not be empty")
        wanted = call.data.get("device")
        for entry in hass.config_entries.async_entries(DOMAIN):
            coordinator = getattr(getattr(entry, "runtime_data", None), "coordinator", None)
            if coordinator is None or not coordinator.data:
                continue
            for device_id, dev in coordinator.data.items():
                known = (dev or {}).get("fields") or {}
                if (wanted and device_id == wanted) or (not wanted and all(k in known for k in fields)):
                    LOGGER.warning("pentair_pool.set_fields %s -> %s", device_id, fields)
                    await coordinator.async_set_fields(device_id, fields)
                    return
        raise ServiceValidationError("no Pentair device matches those fields")

    if not hass.services.has_service(DOMAIN, SERVICE_SET_FIELDS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_FIELDS,
            handle_set_fields,
            schema=vol.Schema({vol.Required("fields"): {str: vol.Any(str, int, float)}, vol.Optional("device"): str}),
        )
    if not hass.services.has_service(DOMAIN, SERVICE_RELOAD_DATA):
        hass.services.async_register(DOMAIN, SERVICE_RELOAD_DATA, handle_reload_data)
    LOGGER.debug("pentair_pool services registered")
