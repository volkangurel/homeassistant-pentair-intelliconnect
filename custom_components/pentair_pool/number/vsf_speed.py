"""IntelliFlo VSF pump set speeds (`ifd29`-`ifd32` programs, `ifd4`-`ifd7` presets)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import (
    FIELD_IFD4,
    FIELD_IFD5,
    FIELD_IFD6,
    FIELD_IFD7,
    FIELD_IFD29,
    FIELD_IFD30,
    FIELD_IFD31,
    FIELD_IFD32,
    VSF_MAX_RPM,
    VSF_MIN_RPM,
    VSF_RPM_STEP,
)
from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import REVOLUTIONS_PER_MINUTE

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator


def _desc(key: str) -> NumberEntityDescription:
    return NumberEntityDescription(
        key=key,
        translation_key=key,
        icon="mdi:pump",
        native_min_value=VSF_MIN_RPM,
        native_max_value=VSF_MAX_RPM,
        native_step=VSF_RPM_STEP,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        has_entity_name=True,
    )


# (field, description, fallback name)
VSF_SPEED_NUMBERS: tuple[tuple[str, NumberEntityDescription, str], ...] = (
    (FIELD_IFD29, _desc("vsf_program_1_speed"), "VSF program 1 speed"),
    (FIELD_IFD30, _desc("vsf_program_2_speed"), "VSF program 2 speed"),
    (FIELD_IFD31, _desc("vsf_program_3_speed"), "VSF program 3 speed"),
    (FIELD_IFD32, _desc("vsf_program_4_speed"), "VSF program 4 speed"),
    (FIELD_IFD4, _desc("vsf_speed_1_preset"), "VSF speed 1 preset"),
    (FIELD_IFD5, _desc("vsf_speed_2_preset"), "VSF speed 2 preset"),
    (FIELD_IFD6, _desc("vsf_speed_3_preset"), "VSF speed 3 preset"),
    (FIELD_IFD7, _desc("vsf_speed_4_preset"), "VSF speed 4 preset"),
)


def _snap(value: float) -> int:
    """Round to the pump's RPM step and clamp to its range."""
    rpm = int(round(value / VSF_RPM_STEP) * VSF_RPM_STEP)
    return max(VSF_MIN_RPM, min(VSF_MAX_RPM, rpm))


class PentairPoolVsfSpeed(NumberEntity, PentairPoolEntity):
    """One configured IntelliFlo VSF set speed (RPM)."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: PentairPoolDataUpdateCoordinator,
        device_id: str,
        field: str,
        description: NumberEntityDescription,
        name: str,
    ) -> None:
        """Bind to one device field."""
        super().__init__(coordinator, description, device_id)
        self._field = field
        self._attr_name = name

    @property
    def native_value(self) -> float | None:
        """Configured speed."""
        v = self.field_value(self._field)
        if v is None:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Write a new set speed."""
        await self.coordinator.async_set_fields(self._device_id, {self._field: _snap(value)})
