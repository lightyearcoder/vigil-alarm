"""Release 0.7.0: a sensor that watches a number (freezer, fridge, room, mains voltage)."""

from __future__ import annotations

import pytest

from .common import PANEL, make_entry, sub
from .test_integration import _setup, _tick
from .test_panel import _client, _ws


def _freezer(**extra):
    data = {"entity_id": "sensor.freezer", "cls": "silent24", "max_value": -15, "for_seconds": 1800, **extra}
    return sub("zone", "Freezer", data, "freezer")


async def _house(hass, **extra):
    hass.states.async_set("sensor.freezer", "-20")
    entry = await _setup(hass, make_entry(extra_subentries=(_freezer(**extra),)))
    return entry.runtime_data


def _kinds(manager):
    return [e["event"] for e in manager.eventlog.entries]


async def test_a_freezer_that_stays_too_warm_gives_a_technical_alarm(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("sensor.freezer", "-10")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 1700)
    assert manager.snapshot()["technical_alarms"] == []  # not long enough yet
    await _tick(hass, freezer, 120)
    assert manager.snapshot()["technical_alarms"] == ["Freezer"]
    assert hass.states.get(PANEL).state == "disarmed"  # a technical alarm never changes the alarm state
    assert "technical_alarm_started" in _kinds(manager)
    hass.states.async_set("sensor.freezer", "-18")
    await hass.async_block_till_done()
    assert manager.snapshot()["technical_alarms"] == []  # back within the limit: closed at once
    assert "technical_alarm_ended" in _kinds(manager)


async def test_a_short_peak_gives_nothing(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("sensor.freezer", "-5")  # the door is open for a moment
    await hass.async_block_till_done()
    await _tick(hass, freezer, 600)
    hass.states.async_set("sensor.freezer", "-19")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 3000)
    assert manager.snapshot()["technical_alarms"] == []
    assert "technical_alarm_started" not in _kinds(manager)


async def test_the_time_runs_from_the_first_value_outside_the_limit(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("sensor.freezer", "-10")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 1000)
    hass.states.async_set("sensor.freezer", "-8")  # still too warm: the time does not start over
    await hass.async_block_till_done()
    await _tick(hass, freezer, 850)
    assert manager.snapshot()["technical_alarms"] == ["Freezer"]


async def test_no_time_means_at_once_and_a_lower_limit_works(hass, freezer):
    hass.states.async_set("sensor.tank", "25")
    tank = sub("zone", "Fish tank", {"entity_id": "sensor.tank", "cls": "silent24",
                                      "min_value": 22, "max_value": 28, "for_seconds": 0}, "tank")
    manager = (await _setup(hass, make_entry(extra_subentries=(tank,)))).runtime_data
    hass.states.async_set("sensor.tank", "19.5")
    await hass.async_block_till_done()
    assert manager.snapshot()["technical_alarms"] == ["Fish tank"]
    hass.states.async_set("sensor.tank", "25")
    await hass.async_block_till_done()
    assert manager.snapshot()["technical_alarms"] == []
    hass.states.async_set("sensor.tank", "31")
    await hass.async_block_till_done()
    assert manager.snapshot()["technical_alarms"] == ["Fish tank"]


async def test_a_value_that_is_not_a_number_is_an_unavailable_sensor(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("sensor.freezer", "unavailable")
    await hass.async_block_till_done()
    assert manager.snapshot()["technical_alarms"] == []  # silent24 notifies, it does not raise an alarm
    assert manager.sensor_status("freezer") == "unavailable"
    hass.states.async_set("sensor.freezer", "-20")
    await hass.async_block_till_done()
    assert manager.sensor_status("freezer") == "closed"


async def test_an_unavailable_value_cancels_the_waiting_time(hass, freezer):
    manager = await _house(hass)
    hass.states.async_set("sensor.freezer", "-10")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 900)
    hass.states.async_set("sensor.freezer", "unknown")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 1800)
    assert manager.snapshot()["technical_alarms"] == []


async def test_already_too_warm_at_startup_counts_after_the_time(hass, freezer):
    hass.states.async_set("sensor.freezer", "-3")
    manager = (await _setup(hass, make_entry(extra_subentries=(_freezer(),)))).runtime_data
    await _tick(hass, freezer, 1000)
    assert manager.snapshot()["technical_alarms"] == []
    await _tick(hass, freezer, 900)
    assert manager.snapshot()["technical_alarms"] == ["Freezer"]


async def test_the_form_checks_the_limits(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    base = {"name": "Freezer", "entity_id": "sensor.freezer", "cls": "silent24", "on_unavailable": "default"}

    async def save(**data):
        return (await _ws(client, type="vigil_alarm/save", kind="sensor", data={**base, **data}))["result"]

    assert (await save(cls="water", max_value="-15"))["errors"] == {"cls": "value_needs_technical"}
    assert (await save())["errors"] == {"min_value": "value_needs_limit"}
    assert (await save(min_value="5", max_value="2"))["errors"] == {"max_value": "value_limits_order"}
    assert (await save(max_value="abc"))["errors"] == {"max_value": "not_a_number"}
    assert (await save(max_value="-15", for_seconds="-1"))["errors"] == {"for_seconds": "not_negative"}
    res = await save(max_value="-15", for_seconds="1800")
    assert res["ok"] is True
    from custom_components.vigil_alarm.items import items_of
    data = items_of(entry)[res["id"]].data
    assert data["max_value"] == -15.0 and data["for_seconds"] == 1800.0 and "min_value" not in data


async def test_an_on_off_sensor_keeps_no_limits(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = (await _ws(client, type="vigil_alarm/save", kind="sensor", data={
        "name": "Button", "entity_id": "binary_sensor.panic", "cls": "silent24", "max_value": "3", "for_seconds": "9",
        "on_unavailable": "default"}))["result"]
    assert res["ok"] is True
    from custom_components.vigil_alarm.items import items_of
    assert not {"max_value", "min_value", "for_seconds"} & set(items_of(entry)[res["id"]].data)
