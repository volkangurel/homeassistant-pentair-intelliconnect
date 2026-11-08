"""Binary-sensor platform for pentair_pool."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import (
    FIELD_IFS4,
    FIELD_IFS18,
    FIELD_RA4,
    PARALLEL_UPDATES as PARALLEL_UPDATES,
)

from .pump_running import PentairPoolPumpRunningBinarySensor
from .status import PentairPoolAlarmBinarySensor, PentairPoolOnlineBinarySensor
from .vsf_pump import PentairPoolVsfPumpAlarmBinarySensor, PentairPoolVsfPumpRunningBinarySensor

if TYPE_CHECKING:
    from custom_components.pentair_pool.data import PentairPoolConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PentairPoolConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add per-device binary sensors."""
    coordinator = entry.runtime_data.coordinator
    entities = []
    for device_id, dev in (coordinator.data or {}).items():
        entities.append(PentairPoolOnlineBinarySensor(coordinator, device_id))
        entities.append(PentairPoolAlarmBinarySensor(coordinator, device_id))
        fields = dev.get("fields") or {}
        if FIELD_RA4 in fields:
            entities.append(PentairPoolPumpRunningBinarySensor(coordinator, device_id))
        if FIELD_IFS4 in fields:
            entities.append(PentairPoolVsfPumpRunningBinarySensor(coordinator, device_id))
        if FIELD_IFS18 in fields:
            entities.append(PentairPoolVsfPumpAlarmBinarySensor(coordinator, device_id))
    async_add_entities(entities)
