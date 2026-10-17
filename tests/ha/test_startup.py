"""After a restart of Home Assistant the sensors of MQTT or Zigbee come back a little later than Vigil does."""

from __future__ import annotations

from homeassistant.core import CoreState
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from custom_components.vigil_alarm.manager import SIGNAL_EVENT

from .common import PANEL, make_entry
from .test_integration import _tick

SENSORS = ("front_door", "living_pir", "smoke", "tamper")


async def _start_with(hass, freezer, entry, states):
    """Home Assistant starts; the sensors have the given states (None = not there at all)."""
    hass.set_state(CoreState.not_running)
    entry.add_to_hass(hass)
    seen: list[dict] = []
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), seen.append)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for name, state in states.items():
        if state is not None:
            hass.states.async_set(f"binary_sensor.{name}", state)
    await hass.async_start()
    await hass.async_block_till_done()
    return seen


def _types(seen):
    return [e["type"] for e in seen]


async def test_sensors_that_come_back_a_little_later_are_never_reported_as_lost(hass, freezer):
    entry = make_entry()
    seen = await _start_with(hass, freezer, entry, {"front_door": "off", "living_pir": "unavailable", "smoke": None, "tamper": "off"})
    await _tick(hass, freezer, 11)  # the first moment sensors are trusted
    assert "supervision_lost" not in _types(seen)
    assert hass.states.get(PANEL).state == "disarmed"
    await _tick(hass, freezer, 20)  # MQTT is still starting
    assert "supervision_lost" not in _types(seen)
    hass.states.async_set("binary_sensor.living_pir", "off")
    hass.states.async_set("binary_sensor.smoke", "off")
    await hass.async_block_till_done()
    assert "supervision_lost" not in _types(seen) and "supervision_restored" not in _types(seen)
    settled = [e for e in seen if e["type"] == "startup_settled"]
    assert len(settled) == 1 and settled[0]["unavailable"] == 0
    await _tick(hass, freezer, 200)  # the timer that was waiting is gone: nothing more happens
    assert _types(seen).count("startup_settled") == 1


async def test_a_sensor_that_is_still_gone_when_the_wait_is_over_is_reported_then(hass, freezer):
    entry = make_entry(startup_wait_seconds=60)
    seen = await _start_with(hass, freezer, entry, {"front_door": "off", "living_pir": "unavailable", "smoke": "off", "tamper": "off"})
    await _tick(hass, freezer, 11)
    await _tick(hass, freezer, 30)  # 41 seconds: still waiting
    assert "supervision_lost" not in _types(seen)
    await _tick(hass, freezer, 30)  # 71 seconds: the wait of 60 is over
    lost = [e for e in seen if e["type"] == "supervision_lost"]
    assert [e["sensor_name"] for e in lost] == ["Living PIR"]
    settled = [e for e in seen if e["type"] == "startup_settled"][0]
    assert settled["unavailable"] == 1 and settled["sensors"] == "Living PIR"
    hass.states.async_set("binary_sensor.living_pir", "off")  # and a late sensor is welcomed back normally
    await hass.async_block_till_done()
    assert "supervision_restored" in _types(seen)


async def test_a_sensor_that_flaps_while_starting_is_left_alone_and_open_sensors_count_at_once(hass, freezer):
    entry = make_entry()
    seen = await _start_with(hass, freezer, entry, {"front_door": "on", "living_pir": "unavailable", "smoke": "off", "tamper": "off"})
    await _tick(hass, freezer, 11)
    hass.states.async_set("binary_sensor.smoke", "unavailable")  # MQTT reconnects: smoke goes away for a moment
    await hass.async_block_till_done()
    assert "supervision_lost" not in _types(seen)
    assert entry.runtime_data.engine._rt["front"].value == "open"  # an open sensor is known right away
    hass.states.async_set("binary_sensor.smoke", "off")
    hass.states.async_set("binary_sensor.living_pir", "off")
    await hass.async_block_till_done()
    assert "supervision_lost" not in _types(seen)
    assert _types(seen).count("startup_settled") == 1


async def test_reloading_vigil_while_home_assistant_runs_does_not_wait(hass):
    from .test_integration import _setup

    entry = make_entry()
    entry.add_to_hass(hass)
    seen: list[dict] = []
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), seen.append)
    for name in SENSORS:
        hass.states.async_set(f"binary_sensor.{name}", "unavailable" if name == "living_pir" else "off")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert [e["sensor_name"] for e in seen if e["type"] == "supervision_lost"] == ["Living PIR"]  # real, so at once
    assert "startup_settled" not in _types(seen)


async def test_the_wait_is_a_setting_with_limits(hass, hass_ws_client):
    from .test_panel import _client, _ws

    entry, client = await _client(hass, hass_ws_client)
    snap = (await _ws(client, type="vigil_alarm/get"))["result"]
    data = dict(snap["entry"]["data"])
    assert data["startup_wait_seconds"] == 120
    assert "startup_wait_seconds" in {f["key"] for f in snap["settings_form"] if f["section"] == "startup"}
    for bad in (0, 9, 901, "x"):
        res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "startup_wait_seconds": bad})
        assert res["result"]["errors"] == {"startup_wait_seconds": "startup_wait_range"}
    ok = await _ws(client, type="vigil_alarm/save_settings", data={**data, "startup_wait_seconds": 300})
    assert ok["result"]["ok"] is True
    await hass.async_block_till_done()
    assert hass.config_entries.async_entries("vigil_alarm")[0].data["startup_wait_seconds"] == 300
