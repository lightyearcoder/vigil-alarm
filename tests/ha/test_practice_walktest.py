from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from .common import EVENTS, make_entry
from .test_integration import _call, _setup
from .test_panel import _client, _ws


async def test_practice_mode_triggers_without_siren_or_messages_and_marks_the_log(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    sirens, notes = [], []
    manager.sirens.handle = lambda e: sirens.append(e["type"])
    manager.notifier.handle = lambda e: notes.append(e["type"])
    res = await _ws(client, type="vigil_alarm/practice", enable=True)
    assert res["success"] and manager.practice.active
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert not sirens and set(notes) <= {"practice_started"}  # nothing sounded, nothing sent after it began
    marked = [e for e in manager.eventlog.entries if (e.get("detail") or {}).get("practice")]
    assert {e["event"] for e in marked} >= {"armed", "pending_started"}
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert not manager.practice.active  # one round: the disarm ends it
    assert manager.eventlog.entries[-1]["event"] == "practice_ended"
    assert manager.eventlog.entries[-1]["result"] == "disarmed"


async def test_practice_mode_ends_by_itself_and_only_starts_while_disarmed(hass, hass_ws_client, freezer):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/practice", enable=True)
    assert not res["success"] and not manager.practice.active
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert (await _ws(client, type="vigil_alarm/practice", enable=True))["success"]
    freezer.tick(timedelta(minutes=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not manager.practice.active


async def test_after_practice_the_siren_and_messages_work_again(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    notes = []
    manager.notifier.handle = lambda e: notes.append(e["type"])
    await _ws(client, type="vigil_alarm/practice", enable=True)
    await _ws(client, type="vigil_alarm/practice", enable=False)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    assert "armed" in notes


async def test_the_walk_test_ticks_off_intrusion_sensors_and_lists_the_missed_ones(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    res = await _ws(client, type="vigil_alarm/walktest", action="start")
    assert res["success"] and manager.walktest.active
    intrusion = [s["name"] for s in res["result"]["sensors"]]
    assert intrusion, "the test house has intrusion sensors"
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert any(s["seen"] for s in manager.walktest.status()["sensors"])
    await _ws(client, type="vigil_alarm/walktest", action="stop")
    last = manager.walktest.last
    assert last["reason"] == "stopped" and last["total"] == len(intrusion)
    assert last["seen"] and len(last["seen"]) + len(last["missing"]) == last["total"]
    assert all(m["reason"] in ("no_response", "unavailable") for m in last["missing"])
    ended = manager.eventlog.entries[-1]
    assert ended["event"] == "walktest_finished" and ended["detail"]["total"] == last["total"]


async def test_the_walk_test_does_not_start_while_armed_and_arming_stops_it(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    assert not (await _ws(client, type="vigil_alarm/walktest", action="start"))["success"]
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert (await _ws(client, type="vigil_alarm/walktest", action="start"))["success"]
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    assert not manager.walktest.active and manager.walktest.last["reason"] == "stopped"


async def test_live_data_has_practice_and_walktest(hass, hass_ws_client):
    from custom_components.vigil_alarm.panel import _live

    entry, client = await _client(hass, hass_ws_client)
    live = _live(entry)
    assert live["practice_until"] is None and live["walktest"]["active"] is False
    await _ws(client, type="vigil_alarm/practice", enable=True)
    assert _live(entry)["practice_until"] > 0


async def test_when_practice_runs_out_during_an_alarm_the_siren_and_messages_start(hass, hass_ws_client, freezer):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    await _ws(client, type="vigil_alarm/practice", enable=True)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=120))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert manager.engine.state == "triggered" and manager.practice.active
    sirens, notes = [], []
    manager.sirens.handle = lambda e: sirens.append(e["type"])
    manager.notifier.handle = lambda e: notes.append(e["type"])
    freezer.tick(timedelta(minutes=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not manager.practice.active and manager.engine.state == "triggered"
    assert "triggered" in sirens and "triggered" in notes  # held back until now, let through at the end


async def test_an_armed_alarm_stays_armed_when_practice_runs_out_and_then_works_for_real(hass, hass_ws_client, freezer):
    entry, client = await _client(hass, hass_ws_client)
    manager = entry.runtime_data
    await _ws(client, type="vigil_alarm/practice", enable=True)
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=31))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert not manager.practice.active and manager.engine.state == "armed_home"
    sirens = []
    manager.sirens.handle = lambda e: sirens.append(e["type"])
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=120))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()
    assert "triggered" in sirens
