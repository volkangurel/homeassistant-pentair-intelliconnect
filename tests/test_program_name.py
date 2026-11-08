"""Tests for the editable VSF program-name text entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.text import ATTR_VALUE, DOMAIN as TEXT_DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

NAMES = {f"text.intelliconnect_vsf_program_{i}_name": f"Program {i}" for i in range(1, 5)}


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_program_names(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    for entity_id, name in NAMES.items():
        st = hass.states.get(entity_id)
        assert st is not None, entity_id
        assert st.state == name
        assert st.attributes["max"] == 20


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_rename_program_writes_field(hass: HomeAssistant, config_entry: MockConfigEntry, device_id: str) -> None:
    await _setup(hass, config_entry)
    with patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None) as put:
        await hass.services.async_call(
            TEXT_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "text.intelliconnect_vsf_program_2_name", ATTR_VALUE: "  Night  "},
            blocking=True,
        )
        await hass.async_block_till_done()
    put.assert_awaited_once_with(device_id, {"p6": "Night"})
    assert hass.states.get("text.intelliconnect_vsf_program_2_name").state == "Night"


@pytest.mark.integration
@pytest.mark.usefixtures("mock_pentair")
async def test_blank_name_rejected(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    with (
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_set_fields", return_value=None) as put,
        pytest.raises(ServiceValidationError),
    ):
        await hass.services.async_call(
            TEXT_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: "text.intelliconnect_vsf_program_1_name", ATTR_VALUE: "   "},
            blocking=True,
        )
    put.assert_not_awaited()


@pytest.mark.integration
@pytest.mark.parametrize("device_fields", [{}])
@pytest.mark.usefixtures("mock_pentair")
async def test_no_name_fields_no_entities(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await _setup(hass, config_entry)
    for entity_id in NAMES:
        assert hass.states.get(entity_id) is None
