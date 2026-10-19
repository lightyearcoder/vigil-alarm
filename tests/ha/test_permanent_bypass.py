"""Release 0.5.5: permanent bypass per sensor."""

from __future__ import annotations

from .common import PANEL, make_entry, sub
from .test_integration import _call, _setup, _tick


def _perm():
    return sub(
        "zone", "Broken window",
        {"entity_id": "binary_sensor.broken", "cls": "intrusion", "type": "instant", "sensor_groups": ["g_all"],
         "permanent_bypass": True, "at_arm_open": "bypass"},
        "broken",
    )


async def test_a_permanent_bypass_stays_after_disarming_and_in_the_switch(hass, freezer):
    entry = await _setup(hass, make_entry(extra_subentries=(_perm(),)), closed=("front_door", "living_pir", "smoke", "tamper"))
    hass.states.async_set("binary_sensor.broken", "off")
    await hass.async_block_till_done()
    manager = entry.runtime_data
    await manager.async_bypass("broken", None, is_admin=True, bypass=True, user_id=None)
    assert manager.sensor_is_bypassed("broken")
    await _call(hass, "alarm_arm_away", code="1234")
    await _tick(hass, freezer, 61)
    hass.states.async_set("binary_sensor.broken", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "armed_away"  # the broken window does not count
    await _call(hass, "alarm_disarm", code="1234")
    assert manager.sensor_is_bypassed("broken")  # still bypassed after disarming
    from custom_components.vigil_alarm.panel import _live

    assert [r["name"] for r in _live(entry)["permanent_bypassed"]] == ["Broken window"]  # the Overview names it
    assert hass.states.get(PANEL).attributes["bypassed_sensors"] == ["Broken window"]  # and the card
    await manager.async_bypass("broken", None, is_admin=True, bypass=False, user_id=None)
    assert not manager.sensor_is_bypassed("broken")
    assert _live(entry)["permanent_bypassed"] == []


async def test_the_flag_is_only_kept_for_sensors_that_can_be_bypassed():
    from custom_components.vigil_alarm.const import CONF_PERMANENT_BYPASS
    from custom_components.vigil_alarm.panel import form_schema

    fields = {f["key"]: f for f in form_schema(["home", "away", "night"])["sensor"]}
    shown = fields[CONF_PERMANENT_BYPASS]["show_if"]["cls"]
    assert "fire" not in shown and "gas" not in shown and "intrusion" in shown
