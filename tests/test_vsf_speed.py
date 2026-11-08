"""Tests for the IntelliFlo VSF set-speed number entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pentair_pool.number.vsf_speed import _snap
from homeassistant.components.number import ATTR_VALUE, DOMAIN as NUMBER_DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

SPEED_NUMBERS = {
    "number.intelliconnect_relay_1_pump_speed": ("ra7", "2405"),
    "number.intelliconnect_heater_pump_speed": ("htd3", "2460"),
    "number.intelliconnect_vsf_program_1_speed": ("ifd29", "2405"),
    "number.intelliconnect_vsf_program_2_speed": ("ifd30", "1500"),
    "number.intelliconnect_vsf_program_3_speed": ("ifd31", "2350"),
    "number.intelliconnect_vsf_program_4_speed": ("ifd32", "3110"),
    "number.intelliconnect_vsf_speed_1_preset": ("ifd4", "2470"),
    "number.intelliconnect_vsf_speed_2_preset": ("ifd5", "2030"),
    "number.intelliconnect_vsf_speed_3_preset": ("ifd6", "3095"),
    "number.intelliconnect_vsf_speed_4_preset": ("ifd7", "1005"),
}


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [(2410, 2410), (2412.4, 2410), (2413, 2415), (100, 450), (5000, 3450)],
)
def test_snap(value: float, expected: int) -> None:
    assert _snap(value) == expected


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_vsf_speed_numbers(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    for entity_id, (_field, raw) in SPEED_NUMBERS.items():
        st = hass.states.get(entity_id)
        assert st is not None, entity_id
        assert float(st.state) == float(raw), entity_id
        assert st.attributes["min"] == 450
        assert st.attributes["max"] == 3450
        assert st.attributes["step"] == 5
        assert st.attributes["unit_of_measurement"] == "rpm"


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_set_vsf_speed_writes_field(hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str) -> None:
    await _setup(hass, config_entry)
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None) as put:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "number.intelliconnect_vsf_program_1_speed", ATTR_VALUE: 2410},
            blocking=True,
        )
        await hass.async_block_till_done()
    put.assert_awaited_once_with(device_id, {"ifd29": 2410})
    assert float(hass.states.get("number.intelliconnect_vsf_program_1_speed").state) == 2410


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_set_relay_1_pump_speed_writes_ra7(
    hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str
) -> None:
    await _setup(hass, config_entry)
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None) as put:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "number.intelliconnect_relay_1_pump_speed", ATTR_VALUE: 2412},
            blocking=True,
        )
        await hass.async_block_till_done()
    put.assert_awaited_once_with(device_id, {"ra7": 2410})


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{}])
@pytest.mark.usefixtures("mock_pentair")
async def test_no_vsf_fields_no_numbers(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    for entity_id in SPEED_NUMBERS:
        assert hass.states.get(entity_id) is None, entity_id
