"""Editable IntelliFlo VSF preset operation modes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator

MODE_OPTIONS = {"0": "Manual", "1": "Timer", "2": "Schedule"}


class PentairPoolVsfMode(SelectEntity, PentairPoolEntity):
    """Select Manual, Timer or Schedule without issuing a Start/Stop command."""

    _attr_options = list(MODE_OPTIONS.values())

    def __init__(self, coordinator: PentairPoolDataUpdateCoordinator, device_id: str, speed: int, field: str) -> None:
        """Bind a preset's operation-mode field."""
        super().__init__(
            coordinator,
            SelectEntityDescription(key=f"vsf_speed_{speed}_mode", icon="mdi:pump", has_entity_name=True),
            device_id,
        )
        self._field = field
        self._attr_name = f"VSF speed {speed} mode"

    @property
    def current_option(self) -> str | None:
        """Decode the stored mode, leaving unexpected values unknown."""
        return MODE_OPTIONS.get(self.field_value(self._field))

    async def async_select_option(self, option: str) -> None:
        """Write only the selected preset's operation mode."""
        for raw, name in MODE_OPTIONS.items():
            if name == option:
                await self.coordinator.async_set_fields(self._device_id, {self._field: int(raw)})
                return
        raise ServiceValidationError(f"Unsupported VSF mode: {option}")
