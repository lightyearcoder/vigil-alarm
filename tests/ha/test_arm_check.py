"""Why can't I arm? What stops arming, and arming with the blockers bypassed."""

from __future__ import annotations

import pytest
from homeassistant.core import Context
from custom_components.vigil_alarm.errors import VigilError as ServiceValidationError

from custom_components.vigil_alarm.const import DOMAIN

from .common import PANEL, make_entry, sub, user_data
from .test_integration import _setup
from .test_panel import _client, _ws


def _entry():
    return make_entry(extra_subentries=[
        sub("user", "Cleo", user_data("2468", may_bypass=True, may_bypass_tamper=True), "cleo"),
        sub("user", "Dave", user_data("1357", may_bypass=False), "dave"),
    ])


async def _open(hass, name):
    """An always-on sensor that opens sets off the alarm; after a disarm it is still open: that stops arming."""
    hass.states.async_set(f"binary_sensor.{name}", "on")
    await hass.async_block_till_done()
    await hass.services.async_call(DOMAIN, "disarm", {"code": "1234"}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"


async def _arm(hass, mode="away", **data):
    await hass.services.async_call(DOMAIN, "arm", {"mode": mode, **data}, blocking=True)


async def test_nothing_stops_arming_when_all_is_closed(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/arm_check", mode="away")
    assert res["result"]["blockers"] == []


async def test_an_open_tamper_contact_stops_arming_and_is_named(hass, hass_ws_client):
    entry = await _setup(hass, _entry(), closed=("front_door", "living_pir", "smoke"))
    await _open(hass, "tamper")
    client = await hass_ws_client(hass)
    res = await _ws(client, type="vigil_alarm/arm_check", mode="away")
    blockers = res["result"]["blockers"]
    assert [(b["reason"], b["name"], b["bypassable"]) for b in blockers] == [("alarm_condition", "Tamper", True)]
    live = (await _ws(client, type="vigil_alarm/get"))["success"]
    assert live


async def test_an_open_fire_sensor_stops_arming_and_cannot_be_bypassed(hass, hass_ws_client):
    await _setup(hass, _entry(), closed=("front_door", "living_pir", "tamper"))
    await _open(hass, "smoke")
    client = await hass_ws_client(hass)
    blockers = (await _ws(client, type="vigil_alarm/arm_check", mode="away"))["result"]["blockers"]
    assert [(b["name"], b["bypassable"]) for b in blockers] == [("Smoke", False)]
    with pytest.raises(ServiceValidationError):
        await _arm(hass, code="2468", bypass_open=True)  # fire stays a refusal, whatever the rights
    assert hass.states.get(PANEL).state == "disarmed"


async def test_arm_with_bypass_open_bypasses_the_blocker_and_arms(hass):
    await _setup(hass, _entry(), closed=("front_door", "living_pir", "smoke"))
    await _open(hass, "tamper")
    with pytest.raises(ServiceValidationError):
        await _arm(hass, code="2468")  # without it: refused
    await _arm(hass, code="2468", bypass_open=True)
    state = hass.states.get(PANEL)
    assert state.state == "arming" or state.state.startswith("armed")
    assert "Tamper" in state.attributes["bypassed_sensors"]


async def test_a_user_without_the_right_to_bypass_cannot_use_it(hass):
    await _setup(hass, _entry(), closed=("front_door", "living_pir", "smoke"))
    await _open(hass, "tamper")
    with pytest.raises(ServiceValidationError, match="bypass"):
        await _arm(hass, code="1357", bypass_open=True)  # Dave: may_bypass False
    assert hass.states.get(PANEL).state == "disarmed"
    with pytest.raises(ServiceValidationError, match="tamper"):
        await _arm(hass, code="1234", bypass_open=True)  # Anna: tamper needs its own right
    assert hass.states.get(PANEL).state == "disarmed"


async def test_an_administrator_in_the_ui_may_arm_around_a_blocker(hass, hass_admin_user):
    await _setup(hass, _entry(), closed=("front_door", "living_pir", "smoke"))
    await _open(hass, "tamper")
    await hass.services.async_call(DOMAIN, "arm", {"mode": "away", "code": "1234", "bypass_open": True},
                                   blocking=True, context=Context(user_id=hass_admin_user.id))
    assert "Tamper" in hass.states.get(PANEL).attributes["bypassed_sensors"]


async def test_the_live_view_lists_the_blockers_while_disarmed(hass, hass_ws_client):
    await _setup(hass, _entry(), closed=("front_door", "living_pir", "smoke"))
    await _open(hass, "tamper")
    from custom_components.vigil_alarm.panel import _live
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    live = _live(entry)
    assert set(live["blockers"]) == {"home", "away", "night"}
    hass.states.async_set("binary_sensor.tamper", "off")
    await hass.async_block_till_done()
    assert _live(entry)["blockers"] == {}
