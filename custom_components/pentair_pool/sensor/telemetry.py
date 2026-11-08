"""Read-only telemetry sensors for the IntelliConnect."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from custom_components.pentair_pool.const import (
    FIELD_ECS2,
    FIELD_ECS20,
    FIELD_HTD1,
    FIELD_ICS1,
    FIELD_ICS2,
    FIELD_ICS3,
    FIELD_ICS9,
    FIELD_ICS11,
    FIELD_ICS12,
    FIELD_ICS13,
    FIELD_ICS15,
    FIELD_IFS3,
    FIELD_IFS4,
    FIELD_IFS5,
    FIELD_IFS6,
    FIELD_IFS28,
    FIELD_RA4,
    FIELD_T0,
    FIELD_T1,
    HTD1_LABELS,
)
from custom_components.pentair_pool.entity import PentairPoolEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)

if TYPE_CHECKING:
    from custom_components.pentair_pool.coordinator import PentairPoolDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class PentairSensorDescription(SensorEntityDescription):
    """SensorEntityDescription with a per-field decoder."""

    value_fn: Callable[[str], object] = lambda v: v


def _as_int(v: str) -> int | None:
    try:
        return int(v)
    except TypeError, ValueError:
        return None


def _firmware_hundredths(v: str) -> str | None:
    """Format a firmware version reported as an integer x100 (211 -> "2.11")."""
    n = _as_int(v)
    if n is None or n < 0:
        return v or None
    return f"{n // 100}.{n % 100:02d}"


def _heater_mode_label(v: str) -> str:
    """Map htd1 numeric value to a friendly label."""
    return HTD1_LABELS.get(v, f"Mode {v}")


SENSORS: tuple[tuple[str, PentairSensorDescription], ...] = (
    (
        FIELD_HTD1,
        PentairSensorDescription(
            key="heater_mode",
            translation_key="heater_mode",
            icon="mdi:radiator",
            has_entity_name=True,
            value_fn=_heater_mode_label,
        ),
    ),
    (
        FIELD_T0,
        PentairSensorDescription(
            key="water_temperature",
            translation_key="water_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_T1,
        PentairSensorDescription(
            key="air_temperature",
            translation_key="air_temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_RA4,
        PentairSensorDescription(
            key="filter_pump_power",
            translation_key="filter_pump_power",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.WATT,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    # NOTE: htd14 is exposed by a dedicated countdown entity in sensor/cooldown.py
    # (it ticks locally every second between server updates). Don't duplicate here.
    (
        FIELD_ICS1,
        PentairSensorDescription(
            key="chlorine_actual",
            translation_key="chlorine_actual",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ICS2,
        PentairSensorDescription(
            key="salt_ppm",
            translation_key="salt_ppm",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="ppm",
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ICS9,
        PentairSensorDescription(
            key="salt_cell_temp",
            translation_key="salt_cell_temp",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ICS13,
        PentairSensorDescription(
            key="boost_remaining",
            translation_key="boost_remaining",
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ICS15,
        PentairSensorDescription(
            key="salt_cell_hours",
            translation_key="salt_cell_hours",
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfTime.HOURS,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ICS11,
        PentairSensorDescription(
            key="salt_cell_firmware",
            translation_key="salt_cell_firmware",
            has_entity_name=True,
            value_fn=lambda v: v,
        ),
    ),
    (
        FIELD_ICS12,
        PentairSensorDescription(
            key="salt_cell_model",
            translation_key="salt_cell_model",
            has_entity_name=True,
            value_fn=lambda v: v,
        ),
    ),
    # Raw IntelliChlor error code. Not decoded on purpose: Pentair doesn't
    # document the bit meanings, so we expose the integer as-is.
    (
        FIELD_ICS3,
        PentairSensorDescription(
            key="salt_cell_error_code",
            translation_key="salt_cell_error_code",
            icon="mdi:alert-circle-outline",
            entity_category=EntityCategory.DIAGNOSTIC,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    # --- IntelliFlo VSF variable-speed pump (RS485) ---------------------------
    (
        FIELD_IFS4,
        PentairSensorDescription(
            key="vsf_pump_speed",
            translation_key="vsf_pump_speed",
            icon="mdi:speedometer",
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_IFS3,
        PentairSensorDescription(
            key="vsf_pump_power",
            translation_key="vsf_pump_power",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.WATT,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_IFS6,
        PentairSensorDescription(
            key="vsf_pump_flow",
            translation_key="vsf_pump_flow",
            device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_IFS28,
        PentairSensorDescription(
            key="vsf_pump_model",
            translation_key="vsf_pump_model",
            icon="mdi:pump",
            entity_category=EntityCategory.DIAGNOSTIC,
            has_entity_name=True,
            value_fn=lambda v: v,
        ),
    ),
    (
        FIELD_IFS5,
        PentairSensorDescription(
            key="vsf_pump_firmware",
            translation_key="vsf_pump_firmware",
            icon="mdi:chip",
            entity_category=EntityCategory.DIAGNOSTIC,
            has_entity_name=True,
            value_fn=_firmware_hundredths,
        ),
    ),
    # --- Controller Wi-Fi link -----------------------------------------------
    (
        FIELD_ECS20,
        PentairSensorDescription(
            key="wifi_signal_level",
            translation_key="wifi_signal_level",
            icon="mdi:wifi",
            state_class=SensorStateClass.MEASUREMENT,
            entity_category=EntityCategory.DIAGNOSTIC,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
    (
        FIELD_ECS2,
        PentairSensorDescription(
            key="wifi_rssi",
            translation_key="wifi_rssi",
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            entity_category=EntityCategory.DIAGNOSTIC,
            has_entity_name=True,
            value_fn=_as_int,
        ),
    ),
)


class PentairPoolFieldSensor(SensorEntity, PentairPoolEntity):
    """Generic field-backed sensor."""

    entity_description: PentairSensorDescription

    def __init__(
        self,
        coordinator: PentairPoolDataUpdateCoordinator,
        device_id: str,
        field_code: str,
        description: PentairSensorDescription,
    ) -> None:
        """Bind to one (device, field)."""
        super().__init__(coordinator, description, device_id)
        self._field_code = field_code

    @property
    def native_value(self) -> object:
        """Decode raw field value with the description's value_fn."""
        v = self.field_value(self._field_code)
        if v is None:
            return None
        return self.entity_description.value_fn(v)
