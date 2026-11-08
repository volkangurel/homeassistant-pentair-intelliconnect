"""IntelliFlo VSF (RS485 variable-speed pump) binary sensors.

These read the `ifs*` fields the IntelliConnect reports when an IntelliFlo
VSF pump is attached to its RS485 bus. They're independent of Relay 1
(`ra*`), which may be wired to a different load (e.g. a heater).

- **Running** is derived from `ifs4` (Actual_Speed_Status, RPM) > 0. The
  speed is a physical measurement reported by the pump drive, so it's the
  most direct evidence the motor is turning. `ifs1` (Running_Stopped) is an
  undocumented 0-10 enum (observed `10` while running); it's exposed raw as
  an attribute rather than interpreted.
- **Alarm** is `ifs18` (Alarm, U32) != 0. The bit/code meanings aren't
  documented, so the raw integer is exposed as an attribute and not decoded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import FIELD_IFS1, FIELD_IFS4, FIELD_IFS18, FIELD_IFS30
from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator

RUNNING_DESCRIPTION = BinarySensorEntityDescription(
    key="vsf_pump_running",
    translation_key="vsf_pump_running",
    device_class=BinarySensorDeviceClass.RUNNING,
    has_entity_name=True,
)

ALARM_DESCRIPTION = BinarySensorEntityDescription(
    key="vsf_pump_alarm",
    translation_key="vsf_pump_alarm",
    device_class=BinarySensorDeviceClass.PROBLEM,
    has_entity_name=True,
)


def _as_int(v: str | None) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except TypeError, ValueError:
        return None


class PentairPoolVsfPumpRunningBinarySensor(BinarySensorEntity, PentairPoolEntity):
    """`Actual_Speed_Status (ifs4) > 0` indicator for the VSF pump."""

    def __init__(
        self,
        coordinator: PentairPoolDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Bind to one device."""
        super().__init__(coordinator, RUNNING_DESCRIPTION, device_id)
        self._attr_name = "VSF pump running"

    @property
    def is_on(self) -> bool | None:
        """True when the pump reports a non-zero shaft speed."""
        rpm = _as_int(self.field_value(FIELD_IFS4))
        if rpm is None:
            return None
        return rpm > 0

    @property
    def extra_state_attributes(self) -> dict[str, int | None]:
        """Expose the raw Running_Stopped value (undocumented enum)."""
        return {"running_stopped_raw": _as_int(self.field_value(FIELD_IFS1))}


class PentairPoolVsfPumpAlarmBinarySensor(BinarySensorEntity, PentairPoolEntity):
    """`Alarm (ifs18) != 0` indicator for the VSF pump."""

    def __init__(
        self,
        coordinator: PentairPoolDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Bind to one device."""
        super().__init__(coordinator, ALARM_DESCRIPTION, device_id)
        self._attr_name = "VSF pump alarm"

    @property
    def is_on(self) -> bool | None:
        """True when the pump reports a non-zero alarm code."""
        code = _as_int(self.field_value(FIELD_IFS18))
        if code is None:
            return None
        return code != 0

    @property
    def extra_state_attributes(self) -> dict[str, int | None]:
        """Expose the raw (undecoded) alarm code and the over-temperature flag."""
        attrs: dict[str, int | None] = {"alarm_code": _as_int(self.field_value(FIELD_IFS18))}
        if FIELD_IFS30 in self.fields:
            attrs["temp_alarm_higher_than_150"] = _as_int(self.field_value(FIELD_IFS30))
        return attrs
