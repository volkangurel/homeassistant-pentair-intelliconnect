"""Read-only active-preset sensor tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

ENTITY = "sensor.intelliconnect_vsf_active_speed"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("menu", "expected"),
    [
        ("0", "Stopped"),
        ("1", "Speed 1"),
        ("2", "Speed 2"),
        ("3", "Speed 3"),
        ("4", "Speed 4"),
        ("9", "Other"),
        ("15", "Other"),
        ("bad", "unknown"),
    ],
)
@pytest.mark.usefixtures("mock_pentair")
async def test_menu_decode(
    hass: HomeAssistant, config_entry: MockConfigEntry, device_fields: dict, menu: str, expected: str
) -> None:
    device_fields["ifs2"]["value"] = menu
    device_fields["ifs27"]["value"] = "130"
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields") as put:
        await _setup(hass, config_entry)
    put.assert_not_awaited()
    state = hass.states.get(ENTITY)
    assert state.state == expected
    assert state.attributes["active_menu"] == (int(menu) if menu != "bad" else None)
    assert state.attributes["minutes_left"] == (0 if menu == "0" else 130)


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_ws_updates_and_stale_menu_when_stopped(
    hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str
) -> None:
    await _setup(hass, config_entry)
    c = config_entry.runtime_data.coordinator
    await c._handle_ws_update(device_id, {"ifs2": {"value": "1"}, "ifs27": {"value": "130"}})  # noqa: SLF001
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "Speed 1"
    assert hass.states.get(ENTITY).attributes["minutes_left"] == 130
    await c._handle_ws_update(device_id, {"ifs1": {"value": "4"}})  # noqa: SLF001
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "Stopped"
    assert hass.states.get(ENTITY).attributes["minutes_left"] == 0
    assert hass.states.get(ENTITY).attributes["active_menu"] == 1


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{"ifs2": {"value": "1"}, "ifs27": {"value": "bad"}}])
@pytest.mark.usefixtures("mock_pentair")
async def test_invalid_duration(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    assert hass.states.get(ENTITY).state == "Speed 1"
    assert hass.states.get(ENTITY).attributes["minutes_left"] is None


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{}])
@pytest.mark.usefixtures("mock_pentair")
async def test_no_menu_no_sensor(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    assert hass.states.get(ENTITY) is None
