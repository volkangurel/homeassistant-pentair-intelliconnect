"""Tests for VSF preset modes, local schedules and timer durations."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pentair_pool.const import VSF_PRESET_FIELDS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_preset_states_no_writes(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    # Intentionally far from UTC; VSF times must not be shifted like relay times.
    await hass.config.async_update(time_zone="America/New_York")
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields") as put:
        await _setup(hass, config_entry)
    put.assert_not_awaited()
    for speed, mode, start, stop, duration in (
        (1, "Schedule", "08:00:00", "18:00:00", 10),
        (2, "Timer", "00:00:00", "00:01:00", 2),
        (3, "Manual", "00:00:00", "00:01:00", 4),
        (4, "Manual", "09:00:00", "17:00:00", 10),
    ):
        root = f"intelliconnect_vsf_speed_{speed}"
        state = hass.states.get(f"select.{root}_mode")
        assert state.state == mode
        assert state.attributes["options"] == ["Manual", "Timer", "Schedule"]
        assert hass.states.get(f"time.{root}_start").state == start
        assert hass.states.get(f"time.{root}_stop").state == stop
        timer = hass.states.get(f"number.{root}_timer_duration")
        assert float(timer.state) == duration
        assert timer.attributes["min"] == -1
        assert timer.attributes["max"] == 600
        assert timer.attributes["step"] == 1
        assert timer.attributes["unit_of_measurement"] == "min"


@pytest.mark.integration
@pytest.mark.parametrize(("speed", "mode_field", "start_field", "stop_field", "timer_field"), VSF_PRESET_FIELDS)
@pytest.mark.usefixtures("mock_pentair")
async def test_each_preset_writes_only_correct_field(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_id: str,
    *,
    speed: int,
    mode_field: str,
    start_field: str,
    stop_field: str,
    timer_field: str,
) -> None:
    await _setup(hass, config_entry)
    root = f"intelliconnect_vsf_speed_{speed}"
    cases = [
        ("select", "select_option", f"{root}_mode", {"option": "Manual"}, mode_field, 0),
        ("select", "select_option", f"{root}_mode", {"option": "Timer"}, mode_field, 1),
        ("select", "select_option", f"{root}_mode", {"option": "Schedule"}, mode_field, 2),
        ("time", "set_value", f"{root}_start", {"time": "23:59:00"}, start_field, 1439),
        ("time", "set_value", f"{root}_stop", {"time": "00:00:00"}, stop_field, 0),
        ("number", "set_value", f"{root}_timer_duration", {"value": 600}, timer_field, 600),
        ("number", "set_value", f"{root}_timer_duration", {"value": -1}, timer_field, -1),
    ]
    for domain, service, entity, data, field, value in cases:
        with patch(
            "custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None
        ) as put:
            await hass.services.async_call(domain, service, {"entity_id": f"{domain}.{entity}", **data}, blocking=True)
            await hass.async_block_till_done()
        put.assert_awaited_once_with(device_id, {field: value})


@pytest.mark.integration
@pytest.mark.parametrize(
    ("domain", "service", "entity", "data"),
    [
        ("select", "select_option", "mode", {"option": "Invalid"}),
        ("time", "set_value", "start", {"time": "08:00:01"}),
        ("number", "set_value", "timer_duration", {"value": 601}),
        ("number", "set_value", "timer_duration", {"value": -2}),
        ("number", "set_value", "timer_duration", {"value": 1.5}),
    ],
)
@pytest.mark.usefixtures("mock_pentair")
async def test_invalid_values_never_write(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    *,
    domain: str,
    service: str,
    entity: str,
    data: dict,
) -> None:
    await _setup(hass, config_entry)
    with (
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields") as put,
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            domain, service, {"entity_id": f"{domain}.intelliconnect_vsf_speed_1_{entity}", **data}, blocking=True
        )
    put.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{}])
@pytest.mark.usefixtures("mock_pentair")
async def test_absent_fields_no_preset_controls(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    assert not [s.entity_id for s in hass.states.async_all() if "vsf_speed_" in s.entity_id]


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{"ifd11": {"value": "1439"}}])
@pytest.mark.usefixtures("mock_pentair")
async def test_partial_fields_create_only_reported_control(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    states = [s for s in hass.states.async_all() if "vsf_speed_" in s.entity_id]
    assert [(s.entity_id, s.state) for s in states] == [("time.intelliconnect_vsf_speed_4_start", "23:59:00")]


@pytest.mark.integration
@pytest.mark.parametrize(
    "device_fields",
    [
        {
            "ifd0": {"value": "3"},
            "ifd8": {"value": "1440"},
            "ifd12": {"value": "bad"},
            "ifd16": {"value": None},
        }
    ],
)
@pytest.mark.usefixtures("mock_pentair")
async def test_malformed_fields_unknown(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    for entity in (
        "select.intelliconnect_vsf_speed_1_mode",
        "time.intelliconnect_vsf_speed_1_start",
        "time.intelliconnect_vsf_speed_1_stop",
        "number.intelliconnect_vsf_speed_1_timer_duration",
    ):
        assert hass.states.get(entity).state == "unknown"
