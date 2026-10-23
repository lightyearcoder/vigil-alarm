from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from .common import make_entry
from .test_discovery import _add, _device
from .test_integration import _setup
from .test_panel import _client, _ws


async def _tick(hass, freezer, seconds=6):
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


async def test_a_sensor_that_appears_later_is_announced_once(hass, freezer):
    entry = await _setup(hass, make_entry())
    manager = entry.runtime_data
    assert manager.new_sensors.count == 0
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "new_window", _device(hass, other, "w1", "New window"), "window")
    await _tick(hass, freezer)
    assert [e["entity_id"] for e in manager.new_sensors.entities] == ["binary_sensor.new_window"]
    await manager.new_sensors.async_dismiss()
    assert manager.new_sensors.count == 0
    await _tick(hass, freezer)
    assert manager.new_sensors.count == 0  # not announced again


async def test_what_exists_at_the_first_start_is_not_new_when_there_are_sensors(hass):
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "old_pir", None, "motion")
    entry = await _setup(hass, make_entry())
    assert entry.runtime_data.new_sensors.count == 0


async def test_the_new_sensors_are_part_of_the_live_data_and_can_be_dismissed(hass, hass_ws_client, freezer):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "new_door", None, "door")
    await _tick(hass, freezer)
    res = await _ws(client, type="vigil_alarm/new_sensors_dismiss")
    assert res["success"]
    assert entry.runtime_data.new_sensors.count == 0


async def test_an_ignored_entity_is_hidden_from_the_notice_and_can_be_restored(hass, hass_ws_client, freezer):
    entry, client = await _client(hass, hass_ws_client)
    other = MockConfigEntry(domain="test")
    other.add_to_hass(hass)
    _add(hass, other, "binary_sensor", "room_motion", None, "motion")
    await _tick(hass, freezer)
    assert entry.runtime_data.new_sensors.count == 1
    res = await _ws(client, type="vigil_alarm/discover_ignore", entity_ids=["binary_sensor.room_motion"], ignore=True)
    assert res["success"]
    assert entry.runtime_data.new_sensors.count == 0
    found = (await _ws(client, type="vigil_alarm/discover"))["result"]
    row = next(c for c in found["candidates"] if c["entity_id"] == "binary_sensor.room_motion")
    assert row["ignored"] is True
    # it survives a restart: the store holds it
    assert "binary_sensor.room_motion" in (await entry.runtime_data.new_sensors._store.async_load())["ignored"]
    await _ws(client, type="vigil_alarm/discover_ignore", entity_ids=["binary_sensor.room_motion"], ignore=False)
    found = (await _ws(client, type="vigil_alarm/discover"))["result"]
    assert next(c for c in found["candidates"] if c["entity_id"] == "binary_sensor.room_motion")["ignored"] is False
