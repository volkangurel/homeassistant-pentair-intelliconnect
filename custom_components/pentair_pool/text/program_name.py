"""IntelliFlo VSF program display name (`p5`-`p8`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import FIELD_P5, FIELD_P6, FIELD_P7, FIELD_P8, PROGRAM_NAME_MAX_LEN
from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator

PROGRAM_NAME_FIELDS: tuple[tuple[int, str], ...] = ((1, FIELD_P5), (2, FIELD_P6), (3, FIELD_P7), (4, FIELD_P8))


class PentairPoolProgramName(TextEntity, PentairPoolEntity):
    """Editable name of one VSF program, as shown in the Pentair Home app."""

    _attr_native_min = 1
    _attr_native_max = PROGRAM_NAME_MAX_LEN

    def __init__(
        self,
        coordinator: PentairPoolDataUpdateCoordinator,
        device_id: str,
        field: str,
        number: int,
    ) -> None:
        """Bind to one program-name field."""
        description = TextEntityDescription(
            key=f"vsf_program_{number}_name",
            translation_key=f"vsf_program_{number}_name",
            icon="mdi:rename",
            has_entity_name=True,
        )
        super().__init__(coordinator, description, device_id)
        self._field = field
        self._attr_name = f"VSF program {number} name"

    @property
    def native_value(self) -> str | None:
        """Current program name."""
        return self.field_value(self._field)

    async def async_set_value(self, value: str) -> None:
        """Rename the program."""
        name = value.strip()
        if not name:
            raise ServiceValidationError("Program name can't be empty")
        await self.coordinator.async_set_fields(self._device_id, {self._field: name[:PROGRAM_NAME_MAX_LEN]})
