from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.vigil.items import items_of
from custom_components.vigil.const import DOMAIN
from custom_components.vigil.credentials import code_matches

from .common import make_entry

ENTRY_INPUT = {
    "name": "Home alarm",
    "modes": ["home", "away"],
    "exit_delay_home": 0,
    "exit_delay_away": 45,
    "exit_delay_night": 10,
    "default_entry_delay": 20,
    "trigger_time": 0,
    "code_arm_required": True,
}


async def test_create_entry_and_only_one_allowed(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home alarm" and result["data"]["exit_delay_away"] == 45
    again = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert again["type"] is FlowResultType.ABORT


async def test_entry_needs_a_mode(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**ENTRY_INPUT, "modes": []})
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "no_modes"}


async def test_a_new_alarm_starts_with_two_sensor_groups(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], ENTRY_INPUT)
    entry = result["result"]
    groups = {s.title: s.data for s in items_of(entry).values() if s.subentry_type == "sensor_group"}
    assert set(groups) == {"Perimeter", "Interior"}
    assert groups["Perimeter"] == {"modes": ["home", "away"], "suggest_for": "contacts"}
    assert groups["Interior"] == {"modes": ["away"], "suggest_for": "motion"}


async def test_there_are_no_standard_forms_for_the_parts(hass):
    # Sensors, users and the rest are edited in the Vigil panel only.
    from custom_components.vigil.config_flow import VigilConfigFlow

    entry = make_entry(users=False)
    assert VigilConfigFlow.async_get_supported_subentry_types(entry) == {}


async def test_reconfigure_the_alarm_itself(hass):
    entry = make_entry(users=False)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_RECONFIGURE, "entry_id": entry.entry_id})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**{k: v for k, v in ENTRY_INPUT.items() if k != "name"}, "exit_delay_away": 77})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "reconfigure_successful"
    assert entry.data["exit_delay_away"] == 77
