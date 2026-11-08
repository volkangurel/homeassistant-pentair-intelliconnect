"""Select platform for IntelliFlo VSF preset operation modes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import PARALLEL_UPDATES as PARALLEL_UPDATES, VSF_PRESET_FIELDS

from .vsf_mode import PentairPoolVsfMode

if TYPE_CHECKING:
    from custom_components.pentair_pool.data import PentairPoolConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant, entry: PentairPoolConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create only the modes reported by each controller."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        PentairPoolVsfMode(coordinator, device_id, speed, field)
        for device_id, dev in (coordinator.data or {}).items()
        for speed, field, _start, _stop, _duration in VSF_PRESET_FIELDS
        if field in (dev.get("fields") or {})
    )
