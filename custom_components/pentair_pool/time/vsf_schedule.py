"""VSF preset schedule times, in local minutes after midnight.

Unlike relay ra1/ra2 schedules, these fields already hold pump wall-clock
minutes, so no UTC or DST offset is applied. The pump has minute precision.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator


class PentairPoolVsfSchedule(TimeEntity, PentairPoolEntity):
    """One VSF preset's local start or stop time."""

    def __init__(
        self, coordinator: PentairPoolDataUpdateCoordinator, device_id: str, speed: int, field: str, kind: str
    ) -> None:
        """Bind one minute-of-day field."""
        super().__init__(
            coordinator,
            TimeEntityDescription(key=f"vsf_speed_{speed}_{kind}", icon="mdi:clock-outline", has_entity_name=True),
            device_id,
        )
        self._field = field
        self._attr_name = f"VSF speed {speed} {kind}"

    @property
    def native_value(self) -> dt.time | None:
        """Return the stored wall time, without timezone conversion."""
        try:
            minutes = int(self.field_value(self._field))
        except ValueError, TypeError:
            return None
        if not 0 <= minutes < 1440:
            return None
        return dt.time(minutes // 60, minutes % 60)

    async def async_set_value(self, value: dt.time) -> None:
        """Write minutes; reject sub-minute values rather than silently round."""
        if value.second or value.microsecond or value.tzinfo is not None:
            raise ServiceValidationError("VSF schedule times require local time with whole-minute precision")
        await self.coordinator.async_set_fields(self._device_id, {self._field: value.hour * 60 + value.minute})
