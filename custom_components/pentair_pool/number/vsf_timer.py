"""VSF preset egg-timer duration controls (minutes)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator


class PentairPoolVsfTimer(NumberEntity, PentairPoolEntity):
    """Stored timer length, not the currently remaining run time.

    The cloud advertises -1..600 minutes. Preserve the -1 sentinel verbatim;
    do not reinterpret it as a Start, Stop, or unlimited-run command.
    """

    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: PentairPoolDataUpdateCoordinator, device_id: str, speed: int, field: str) -> None:
        """Bind a preset's timer field using the controller's limits."""
        super().__init__(
            coordinator,
            NumberEntityDescription(
                key=f"vsf_speed_{speed}_timer_duration",
                icon="mdi:timer-outline",
                native_min_value=-1,
                native_max_value=600,
                native_step=1,
                native_unit_of_measurement=UnitOfTime.MINUTES,
                has_entity_name=True,
            ),
            device_id,
        )
        self._field = field
        self._attr_name = f"VSF speed {speed} timer duration"
        meta = self.fields.get(field) or {}
        try:
            minimum, maximum = int(meta.get("min", -1)), int(meta.get("max", 600))
        except ValueError, TypeError:
            minimum, maximum = -1, 600
        if minimum <= maximum:
            self._attr_native_min_value = minimum
            self._attr_native_max_value = maximum

    @property
    def native_value(self) -> float | None:
        """Return the configured whole-minute timer duration."""
        try:
            return int(self.field_value(self._field))
        except ValueError, TypeError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Write an integral duration within the controller-advertised range."""
        if not math.isfinite(value) or value != int(value):
            raise ServiceValidationError("VSF timer duration must be a whole number of minutes")
        if not self.native_min_value <= value <= self.native_max_value:
            raise ServiceValidationError("VSF timer duration is outside the controller's range")
        await self.coordinator.async_set_fields(self._device_id, {self._field: int(value)})
