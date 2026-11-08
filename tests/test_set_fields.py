"""Tests for the advanced raw-field service (all cloud writes mocked)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.integration
@pytest.mark.parametrize("explicit", [True, False])
@pytest.mark.usefixtures("mock_pentair")
async def test_raw_service_routes_and_stringifies(
    hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str, explicit: bool
) -> None:
    await _setup(hass, config_entry)
    data = {"fields": {"ifd3": 2, "ifd11": "600"}}
    if explicit:
        data["device"] = device_id
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None) as put:
        await hass.services.async_call("pentair_pool", "set_fields", data, blocking=True)
    put.assert_awaited_once_with(device_id, {"ifd3": "2", "ifd11": "600"})


@pytest.mark.integration
@pytest.mark.parametrize(
    "data", [{"fields": {}}, {"fields": {"nonexistent": "1"}}, {"fields": {"ifd3": "2"}, "device": "missing"}]
)
@pytest.mark.usefixtures("mock_pentair")
async def test_no_matching_device_never_writes(hass: HomeAssistant, config_entry: MockConfigEntry, data: dict) -> None:
    await _setup(hass, config_entry)
    with (
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields") as put,
        pytest.raises(ServiceValidationError),
    ):
        await hass.services.async_call("pentair_pool", "set_fields", data, blocking=True)
    put.assert_not_awaited()
