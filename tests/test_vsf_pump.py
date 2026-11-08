"""Tests for the IntelliFlo VSF pump, salt-cell error and Wi-Fi entities."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pentair_pool.sensor.telemetry import _firmware_hundredths
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

NEW_SENSORS = {
    "sensor.intelliconnect_vsf_pump_speed": ("2405", "rpm"),
    "sensor.intelliconnect_vsf_pump_power": ("673", "W"),
    "sensor.intelliconnect_vsf_pump_flow": ("36", "gal/min"),
    "sensor.intelliconnect_vsf_pump_model": ("Intelli VSF", None),
    "sensor.intelliconnect_vsf_pump_firmware": ("2.11", None),
    "sensor.intelliconnect_salt_cell_error_code": ("128", None),
    "sensor.intelliconnect_wi_fi_signal_level": ("1", None),
    "sensor.intelliconnect_wi_fi_rssi": ("-78", "dBm"),
}

DIAGNOSTIC = {
    "sensor.intelliconnect_vsf_pump_model",
    "sensor.intelliconnect_vsf_pump_firmware",
    "sensor.intelliconnect_salt_cell_error_code",
    "sensor.intelliconnect_wi_fi_signal_level",
    "sensor.intelliconnect_wi_fi_rssi",
}


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("211", "2.11"), ("5", "0.05"), ("1000", "10.00"), ("abc", "abc"), ("", None)],
)
def test_firmware_hundredths(raw: str, expected: str | None) -> None:
    assert _firmware_hundredths(raw) == expected


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_vsf_sensors(hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str) -> None:
    await _setup(hass, config_entry)
    registry = er.async_get(hass)

    for entity_id, (state, unit) in NEW_SENSORS.items():
        st = hass.states.get(entity_id)
        assert st is not None, entity_id
        assert st.state == state, entity_id
        assert st.attributes.get("unit_of_measurement") == unit, entity_id
        entry = registry.async_get(entity_id)
        assert entry is not None
        assert entry.unique_id.startswith(f"{device_id}_")
        expected_cat = EntityCategory.DIAGNOSTIC if entity_id in DIAGNOSTIC else None
        assert entry.entity_category == expected_cat, entity_id

    assert hass.states.get("sensor.intelliconnect_vsf_pump_power").attributes["device_class"] == "power"
    assert hass.states.get("sensor.intelliconnect_vsf_pump_flow").attributes["device_class"] == "volume_flow_rate"
    assert hass.states.get("sensor.intelliconnect_wi_fi_rssi").attributes["device_class"] == "signal_strength"


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_vsf_binary_sensors(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)

    running = hass.states.get("binary_sensor.intelliconnect_vsf_pump_running")
    assert running is not None
    assert running.state == "on"
    assert running.attributes["device_class"] == "running"
    assert running.attributes["running_stopped_raw"] == 10

    alarm = hass.states.get("binary_sensor.intelliconnect_vsf_pump_alarm")
    assert alarm is not None
    assert alarm.state == "off"
    assert alarm.attributes["device_class"] == "problem"
    assert alarm.attributes["alarm_code"] == 0
    assert alarm.attributes["temp_alarm_higher_than_150"] == 0

    # Relay 1 isn't reported -> no relay-based pump entities.
    assert hass.states.get("binary_sensor.intelliconnect_filter_pump_running") is None


@pytest.mark.integration
async def test_ws_push_updates_vsf_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_pentair: None,
    device_id: str,
) -> None:
    await _setup(hass, config_entry)
    coordinator = config_entry.runtime_data.coordinator

    await coordinator._handle_ws_update(  # noqa: SLF001
        device_id,
        {
            "ifs4": {"value": "0"},
            "ifs3": {"value": "0"},
            "ifs18": {"value": "4"},
        },
    )
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.intelliconnect_vsf_pump_running").state == "off"
    assert hass.states.get("sensor.intelliconnect_vsf_pump_speed").state == "0"
    assert hass.states.get("sensor.intelliconnect_vsf_pump_power").state == "0"
    alarm = hass.states.get("binary_sensor.intelliconnect_vsf_pump_alarm")
    assert alarm.state == "on"
    assert alarm.attributes["alarm_code"] == 4


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{}])
@pytest.mark.usefixtures("mock_pentair")
async def test_no_vsf_fields_no_entities(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Controllers without a VSF pump / Wi-Fi fields must not get orphan entities."""
    await _setup(hass, config_entry)

    for entity_id in [
        *NEW_SENSORS,
        "binary_sensor.intelliconnect_vsf_pump_running",
        "binary_sensor.intelliconnect_vsf_pump_alarm",
    ]:
        assert hass.states.get(entity_id) is None, entity_id
