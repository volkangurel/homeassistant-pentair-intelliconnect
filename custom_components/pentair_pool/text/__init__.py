"""Text platform: editable IntelliFlo VSF program names (`p5`-`p8`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import PARALLEL_UPDATES as PARALLEL_UPDATES

from .program_name import PROGRAM_NAME_FIELDS, PentairPoolProgramName

if TYPE_CHECKING:
    from custom_components.pentair_pool.data import PentairPoolConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """One text entity per program-name field the controller reports."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        PentairPoolProgramName(coordinator, device_id, field, number)
        for device_id, dev in (coordinator.data or {}).items()
        for number, field in PROGRAM_NAME_FIELDS
        if field in (dev.get("fields") or {})
    )
