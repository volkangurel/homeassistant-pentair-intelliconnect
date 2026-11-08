"""Read-only IntelliFlo VSF active preset and remaining duration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import FIELD_IFS1, FIELD_IFS2, FIELD_IFS27
from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator


class PentairPoolVsfActiveSpeed(SensorEntity, PentairPoolEntity):
    """Decode Active_Menu without confusing external programs with presets.

    0 is stopped; preset menus 1..4 identify Speed 1..4. Other menu codes
    are deliberately not guessed: retain the raw code as an attribute.
    """

    def __init__(self, coordinator: PentairPoolDataUpdateCoordinator, device_id: str) -> None:
        """Bind to the controller's read-only VSF status fields."""
        super().__init__(
            coordinator,
            SensorEntityDescription(
                key="vsf_active_speed",
                icon="mdi:pump",
                device_class=SensorDeviceClass.ENUM,
                options=["Stopped", "Speed 1", "Speed 2", "Speed 3", "Speed 4", "Other"],
                has_entity_name=True,
            ),
            device_id,
        )
        self._attr_name = "VSF active speed"

    def _integer_field(self, field: str) -> int | None:
        """Decode status fields defensively."""
        try:
            return int(self.field_value(field))
        except TypeError, ValueError:
            return None

    @property
    def native_value(self) -> str | None:
        """Return the selected preset, or stopped even if a stale menu remains."""
        menu = self._integer_field(FIELD_IFS2)
        if self._integer_field(FIELD_IFS1) == 4 or menu == 0:
            return "Stopped"
        if menu is None:
            return None
        if 1 <= menu <= 4:
            return f"Speed {menu}"
        return "Other"

    @property
    def extra_state_attributes(self) -> dict[str, int | None]:
        """Expose the raw menu and firmware-reported minutes remaining."""
        minutes = self._integer_field(FIELD_IFS27)
        if self.native_value == "Stopped":
            minutes = 0
        elif minutes is not None and not 0 <= minutes <= 1440:
            minutes = None
        return {"active_menu": self._integer_field(FIELD_IFS2), "minutes_left": minutes}
