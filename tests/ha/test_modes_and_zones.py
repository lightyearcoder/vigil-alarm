"""Release 0.5.4: the modes vacation and custom, and the zone types 24 hours audible and 24 hours silent."""

from __future__ import annotations

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntityFeature as F
from homeassistant.exceptions import HomeAssistantError

from .common import PANEL, make_entry, sub
from .test_integration import _call, _setup, _tick

FIVE = {
    "modes": ["home", "away", "night", "vacation", "custom"],
    "exit_delay_vacation": 60,
    "exit_delay_custom": 30,
}


def _groups():
    return (
        sub("sensor_group", "Vacation", {"modes": ["vacation"]}, "g_vac"),
        sub("sensor_group", "Custom", {"modes": ["custom"]}, "g_custom"),
    )


async def test_the_entity_offers_vacation_and_custom_when_they_are_on(hass):
    await _setup(hass, make_entry(**FIVE))
    features = hass.states.get(PANEL).attributes["supported_features"]
    assert features & F.ARM_VACATION and features & F.ARM_CUSTOM_BYPASS


async def test_the_entity_does_not_offer_them_when_they_are_off(hass):
    await _setup(hass, make_entry())
    features = hass.states.get(PANEL).attributes["supported_features"]
    assert not features & F.ARM_VACATION and not features & F.ARM_CUSTOM_BYPASS
    with pytest.raises(HomeAssistantError):
        await _call(hass, "alarm_arm_vacation", code="1234")


async def test_arming_vacation_and_custom_with_their_own_exit_delays(hass, freezer):
    await _setup(hass, make_entry(extra_subentries=_groups(), **FIVE))
    await _call(hass, "alarm_arm_vacation", code="1234")
    assert hass.states.get(PANEL).state == "arming"
    await _tick(hass, freezer, 61)
    assert hass.states.get(PANEL).state == "armed_vacation"
    await _call(hass, "alarm_disarm", code="1234")
    await _call(hass, "alarm_arm_custom_bypass", code="1234")
    await _tick(hass, freezer, 31)
    assert hass.states.get(PANEL).state == "armed_custom_bypass"  # Home Assistant's name for it
    assert hass.states.get(PANEL).attributes["mode"] == "custom"


async def test_the_arm_service_takes_the_new_modes(hass, freezer):
    await _setup(hass, make_entry(extra_subentries=_groups(), **FIVE))
    await hass.services.async_call(
        "vigil_alarm", "arm", {"mode": "vacation", "code": "1234"}, blocking=True
    )
    await _tick(hass, freezer, 61)
    assert hass.states.get(PANEL).state == "armed_vacation"


async def test_the_panel_profile_has_the_bits_of_the_new_modes(hass):
    await _setup(hass, make_entry(**FIVE))
    from custom_components.vigil_alarm.const import MODE_BITS

    assert MODE_BITS == {"home": 1, "away": 2, "night": 4, "vacation": 8, "custom": 16}


async def test_a_24_hour_audible_zone_goes_off_in_any_state_and_blocks_arming(hass, freezer):
    zone = sub("zone", "Panic button", {"entity_id": "binary_sensor.panic", "cls": "alarm24"}, "panic")
    entry = await _setup(hass, make_entry(extra_subentries=(zone,)))
    manager = entry.runtime_data
    hass.states.async_set("binary_sensor.panic", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "triggered"
    assert hass.states.get(PANEL).attributes["cause"] == "alarm24"
    assert manager.alarmmemory.view()["cause"] == "alarm24"
    await _call(hass, "alarm_disarm", code="1234")
    # still pressed: arming is refused, like with a tamper contact
    with pytest.raises(HomeAssistantError):
        await _call(hass, "alarm_arm_away", code="1234")
    hass.states.async_set("binary_sensor.panic", "off")
    await hass.async_block_till_done()
    await _call(hass, "alarm_arm_away", code="1234")
    assert hass.states.get(PANEL).state == "arming"


async def test_a_24_hour_silent_zone_only_reports(hass, freezer):
    zone = sub("zone", "Silent button", {"entity_id": "binary_sensor.silent", "cls": "silent24"}, "silent")
    entry = await _setup(hass, make_entry(extra_subentries=(zone,)))
    manager = entry.runtime_data
    hass.states.async_set("binary_sensor.silent", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"
    assert manager.snapshot()["technical_alarms"] == ["Silent button"]
    kinds = [e["event"] for e in manager.eventlog.entries]
    assert "technical_alarm_started" in kinds and "triggered" not in kinds


async def test_the_profile_carries_the_last_alarm_as_one_line(hass, freezer):
    entry = await _setup(hass, make_entry())
    manager = entry.runtime_data
    panels = manager.panels
    assert panels._last_alarm_text("en") == ""
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    text = panels._last_alarm_text("en")
    assert text.endswith("Front door") and ":" in text[:5]
    manager.alarmmemory.mark_cancelled()
    assert panels._last_alarm_text("nl").endswith("(vals alarm)")
