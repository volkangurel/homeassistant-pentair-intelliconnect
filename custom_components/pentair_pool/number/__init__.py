"""Number platform for pentair_pool."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import FIELD_ICD1, PARALLEL_UPDATES as PARALLEL_UPDATES

from .chlorine_setpoint import PentairPoolChlorineSetpoint
from .vsf_speed import VSF_SPEED_NUMBERS, PentairPoolVsfSpeed

if TYPE_CHECKING:
    from custom_components.pentair_pool.data import PentairPoolConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import Entity
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the chlorine setpoint and any VSF set speeds the controller reports."""
    coordinator = entry.runtime_data.coordinator
    entities: list[Entity] = []
    for device_id, dev in (coordinator.data or {}).items():
        fields = dev.get("fields") or {}
        if FIELD_ICD1 in fields:
            entities.append(PentairPoolChlorineSetpoint(coordinator, device_id))
        entities.extend(
            PentairPoolVsfSpeed(coordinator, device_id, field, desc, name)
            for field, desc, name in VSF_SPEED_NUMBERS
            if field in fields
        )
    async_add_entities(entities)
