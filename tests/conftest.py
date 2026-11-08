"""Shared fixtures for pentair_pool tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pentair_pool.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

DEVICE_ID = "PNRA1PIF0TEST0001"


def _field(value: str, name: str) -> dict[str, str]:
    return {"value": value, "name": name}


# Trimmed from a real IntelliConnect (PIF0) diagnostics dump with an
# IntelliFlo VSF pump on the RS485 bus. Relay 1 (`ra*`) intentionally absent
# so only the fields under test spawn entities.
VSF_FIELDS: dict[str, dict[str, str]] = {
    "ifs1": _field("10", "Running_Stopped"),
    "ifs2": _field("9", "Active_Menu"),
    "ifs3": _field("673", "Actual_Power"),
    "ifs4": _field("2405", "Actual_Speed_Status"),
    "ifs5": _field("211", "VFD_Software"),
    "ifs6": _field("36", "Actual_Flow_VSF"),
    "ifs18": _field("0", "Alarm"),
    "ifs27": _field("0", "Duration"),
    "ifs28": _field("Intelli VSF", "VFD_Model"),
    "ifs29": _field("0", "External_Control"),
    "ifs30": _field("0", "temp_alarm_higher_than_150"),
    "ifd0": _field("2", "Speed1_Operation_Mode"),
    "ifd1": _field("1", "Speed2_Operation_Mode"),
    "ifd2": _field("0", "Speed3_Operation_Mode"),
    "ifd3": _field("0", "Speed4_Operation_Mode"),
    "ifd8": _field("480", "Speed1_Start_Time"),
    "ifd9": _field("0", "Speed2_Start_Time"),
    "ifd10": _field("0", "Speed3_Start_Time"),
    "ifd11": _field("540", "Speed4_Start_Time"),
    "ifd12": _field("1080", "Speed1_Stop_Time"),
    "ifd13": _field("1", "Speed2_Stop_Time"),
    "ifd14": _field("1", "Speed3_Stop_Time"),
    "ifd15": _field("1020", "Speed4_Stop_Time"),
    "ifd16": {**_field("10", "Speed1_EggTimer_Duration"), "min": "-1", "max": "600"},
    "ifd17": _field("2", "Speed2_EggTimer_Duration"),
    "ifd18": _field("4", "Speed3_EggTimer_Duration"),
    "ifd19": _field("10", "Speed4_EggTimer_Duration"),
    "ifd4": _field("2470", "Speed1_Set_Speed"),
    "ifd5": _field("2030", "Speed2_Set_Speed"),
    "ifd6": _field("3095", "Speed3_Set_Speed"),
    "ifd7": _field("1005", "Speed4_Set_Speed"),
    "ifd29": _field("2405", "Program1_Set_Speed"),
    "ifd30": _field("1500", "Program2_Set_Speed"),
    "ifd31": _field("2350", "Program3_Set_Speed"),
    "ifd32": _field("3110", "Program4_Set_Speed"),
    "ra7": _field("2405", "Relay1_FD_RPM"),
    "htd3": _field("2460", "Heater_FD_RPM"),
    "p5": _field("Program 1", "Program 1"),
    "p6": _field("Program 2", "Program 2"),
    "p7": _field("Program 3", "Program 3"),
    "p8": _field("Program 4", "Program 4"),
    "ics3": _field("128", "Chlor_Error_Message"),
    "ecs2": _field("-78", "rfrssi"),
    "ecs20": _field("1", "WiFiLevel"),
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """Allow loading custom_components/ in every test."""
    return


@pytest.fixture
def device_id() -> str:
    """The mocked controller's device id."""
    return DEVICE_ID


@pytest.fixture
def device_fields() -> dict[str, dict[str, str]]:
    """Fields reported by the mocked controller (override per test)."""
    return {k: dict(v) for k, v in VSF_FIELDS.items()}


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A Pentair config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="test@example.com",
        unique_id="test@example.com",
        data={CONF_USERNAME: "test@example.com", CONF_PASSWORD: "hunter2"},
    )


@pytest.fixture
def mock_pentair(device_fields: dict[str, dict[str, str]]) -> Generator[None]:
    """Mock the Pentair Cloud REST client and skip the WebSocket."""
    listing = {"response": [{"deviceId": DEVICE_ID, "pname": "IntelliConnect", "deviceType": "PIF0"}]}
    detail = {"response": {"data": [{"fields": device_fields, "online": True, "alarm": False}]}}
    with (
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_login", return_value=None),
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_list_devices", return_value=listing),
        patch("custom_components.pentair_pool.api.PentairPoolApiClient.async_get_device", return_value=detail),
        patch(
            "custom_components.pentair_pool.coordinator.base.PentairPoolDataUpdateCoordinator._ensure_ws_started",
            return_value=None,
        ),
    ):
        yield
