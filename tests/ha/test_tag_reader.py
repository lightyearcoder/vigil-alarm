"""The tag reader of a panel: a tag arms and disarms with the rights of the panel and of the user."""

from __future__ import annotations

import json

from custom_components.vigil_alarm.const import READER_EVENT

from .common import EVENTS, PANEL, make_entry, sub, user_data
from .test_integration import _setup
from .test_control_points import _vigil
from .test_panels import _ws, panel_item  # noqa: F401  (the panel item, like the register tests)

TESS = sub("user", "Tess", user_data(None, tags=["04-A1-B2-C3"]), "tess")
BOB = sub("user", "Bob", user_data("5678", allowed_modes=["home"], tags=["04-0B-0B-0B"]), "bob")


async def _scan(hass, tag, reader="vigil-tag-garage"):
    hass.bus.async_fire(READER_EVENT, {"reader": reader, "tag": tag})
    await hass.async_block_till_done()


def _manager(hass):
    return hass.config_entries.async_entries("vigil_alarm")[0].runtime_data


def _forget_the_last_scan(hass):
    _manager(hass).tags._last.clear()


def _house(hass, **reader):
    """A tag reader of its own, and a panel with a screen next to it: the reader needs no panel."""
    data = {"device_kind": "tagreader", "reader_mode": "home", "reader_disarm": True, **reader}
    return _setup(hass, make_entry(extra_subentries=[panel_item("vigil-tag-garage", "Garage reader", "r_garage", None, **data),
                                                     panel_item("hall", "Hall panel", "p_hall"), TESS, BOB], exit_delay_home=0))


async def test_a_tag_arms_and_a_second_scan_disarms(hass):
    await _house(hass)
    await _scan(hass, "04-A1-B2-C3")
    state = hass.states.get(PANEL)
    assert state.state == "armed_home" and state.attributes["changed_by"] == "Tess"
    assert state.attributes["changed_via"] == "vigil-tag-garage"  # the source is the reader, as the panel is with a code
    await _scan(hass, "04-A1-B2-C3")  # the same tag within seconds is the same scan
    assert hass.states.get(PANEL).state == "armed_home"


async def test_a_tag_disarms_when_the_alarm_is_on(hass):
    await _house(hass)
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "armed_home"
    _forget_the_last_scan(hass)  # the same tag within seconds is one scan: this is a later one
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_the_tag_is_written_in_any_way(hass):
    await _house(hass)
    await _scan(hass, "04a1b2c3")  # without the dashes and in lower case
    assert hass.states.get(PANEL).state == "armed_home"


async def test_an_unknown_tag_does_nothing_but_is_logged_and_counts_for_the_lock(hass):
    await _house(hass)
    await _scan(hass, "04-FF-FF-FF")
    assert hass.states.get(PANEL).state == "disarmed"
    events = hass.states.get(EVENTS).attributes
    assert events["event_type"] == "tag_rejected" and events["source"] == "vigil-tag-garage"
    assert "04-FF-FF-FF" not in json.dumps(dict(events))  # the number is never in the log
    assert _manager(hass).lockout.refusal("vigil-tag-garage") is None  # one wrong tag is not a lock yet


async def test_wrong_tags_lock_the_panel_like_wrong_codes(hass):
    await _house(hass)
    for n in range(10):
        await _scan(hass, f"04-FF-FF-{n:02X}")
    assert _manager(hass).lockout.refusal("vigil-tag-garage")  # locked
    await _scan(hass, "04-A1-B2-C3")  # a locked panel does not look at a good tag either
    assert hass.states.get(PANEL).state == "disarmed"


async def test_a_tag_cannot_arm_in_a_mode_the_user_may_not_use(hass):
    await _house(hass, reader_mode="away")  # Bob may only arm in "home"
    await _scan(hass, "04-0B-0B-0B")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_a_tag_that_may_not_disarm_only_arms(hass):
    await _house(hass, reader_disarm=False)
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "armed_home"
    _forget_the_last_scan(hass)
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "armed_home"
    attrs = hass.states.get(EVENTS).attributes
    assert attrs["event_type"] == "panel_refused" and attrs["reason"] == "tag_disarm"


async def test_a_reader_that_belongs_to_no_panel_is_ignored(hass):
    await _house(hass)
    await _scan(hass, "04-A1-B2-C3", reader="some-other-reader")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_a_blocked_panel_does_not_arm_with_a_tag(hass):
    await _house(hass, blocked=True)
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_wrong_tags_on_one_reader_do_not_lock_the_panel_next_to_it(hass):
    await _house(hass)
    for n in range(10):
        await _scan(hass, f"04-FF-FF-{n:02X}")
    assert _manager(hass).lockout.refusal("vigil-tag-garage")
    assert _manager(hass).lockout.refusal("hall") is None  # the panel inside can still be used
    await _vigil(hass, "arm", mode="home", code="1234", source="hall")
    assert hass.states.get(PANEL).state == "armed_home"


async def test_a_reader_stands_alone_and_has_no_profile_of_a_panel(hass):
    await _setup(hass, make_entry(extra_subentries=[
        panel_item("vigil-tag-door", "Door reader", "r_door", None, device_kind="tagreader", reader_mode="home",
                   reader_disarm=True), TESS], exit_delay_home=0))
    await _scan(hass, "04-A1-B2-C3", reader="vigil-tag-door")
    assert hass.states.get(PANEL).state == "armed_home"
    assert hass.states.get("sensor.vigil_tag_door_profile") is None  # a reader has no screen to tell what to show


async def test_a_panel_is_not_a_reader(hass):
    await _setup(hass, make_entry(extra_subentries=[panel_item("hall", "Hall panel", "p_hall"), TESS], exit_delay_home=0))
    await _scan(hass, "04-A1-B2-C3", reader="hall")  # the name of a panel with a screen is not a reader
    assert hass.states.get(PANEL).state == "disarmed"


async def test_the_admin_panel_saves_a_tag_reader_and_checks_it(hass, hass_ws_client):
    from custom_components.vigil_alarm.items import items_of

    entry = await _house(hass)
    client = await hass_ws_client(hass)
    base = {"name": "Hall reader", "device": "tagreader", "panel_id": "vigil-tag-hall", "partitions": ["main"]}
    ok = await _ws(client, type="vigil_alarm/save", kind="panel", data={**base, "reader_mode": "away", "reader_disarm": False})
    assert ok["result"]["ok"] is True, ok
    await hass.async_block_till_done()
    item = next(i for i in items_of(entry).values() if i.subentry_type == "panel" and i.data["panel_id"] == "vigil-tag-hall")
    assert item.data["device_kind"] == "tagreader" and item.data["reader_mode"] == "away"
    assert item.data["reader_disarm"] is False and not item.data.get("ha_user")
    got = (await _ws(client, type="vigil_alarm/get"))["result"]
    form = {f["key"]: f for f in got["forms"]["panel"]}
    assert "tagreader" in form["device"]["options"]
    assert form["reader_mode"]["show_if"] == {"device": ["tagreader"]}
    assert form["language"]["show_if"] == {"device": ["esphome", "account"]}  # a reader has no screen
    for data, errors in (
        ({**base, "name": "Other", "panel_id": "vigil-tag-garage"}, {"panel_id": "panel_id_in_use"}),
        ({**base, "name": "Other", "panel_id": "Bad Name"}, {"panel_id": "panel_id_invalid"}),
        ({**base, "name": "Other", "panel_id": "reader-x", "reader_mode": "disco"}, {"reader_mode": "unknown_choice"}),
    ):
        res = await _ws(client, type="vigil_alarm/save", kind="panel", data=data)
        assert res["result"]["ok"] is False and res["result"]["errors"] == errors, (data, res)


async def test_a_reader_has_a_state_sensor_for_its_leds_that_follows_its_partition(hass):
    await _house(hass, reader_mode="away")
    entity = "sensor.vigil_tag_garage_state"
    assert hass.states.get(entity).state == "disarmed"
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(entity).state == "arming"
    assert hass.states.get("sensor.hall_profile") is not None  # the panel next to it keeps its profile
    assert hass.states.get("sensor.hall_state") is None  # and has no state sensor: only a reader has


async def test_a_reader_of_the_garage_shows_the_garage_and_arms_only_the_garage(hass):
    GARAGE = sub("partition", "Garage", {"modes": ["away"], "exit_delay_away": 0, "default_entry_delay": 0}, "p_gar")
    await _setup(hass, make_entry(extra_subentries=[
        GARAGE, panel_item("vigil-tag-tuin", "Tuin reader", "r_tuin", None, device_kind="tagreader", reader_mode="away",
                           reader_disarm=True, partitions=["p_gar"], default_partition="p_gar"), TESS]))
    await _scan(hass, "04-A1-B2-C3", reader="vigil-tag-tuin")
    assert hass.states.get("sensor.vigil_tag_tuin_state").state == "armed_away"  # the garage, not the house
    assert _manager(hass).partitions["p_gar"].engine.state == "armed_away"
    assert [p.engine.state for pid, p in _manager(hass).partitions.items() if pid != "p_gar"] == ["disarmed"]  # the house
    await _scan(hass, "04-A1-B2-C3", reader="vigil-tag-tuin")  # (the same tag within seconds is one scan)
    _forget_the_last_scan(hass)
    await _scan(hass, "04-A1-B2-C3", reader="vigil-tag-tuin")
    assert hass.states.get("sensor.vigil_tag_tuin_state").state == "disarmed"


async def test_the_state_sensor_of_a_reader_gets_the_id_the_firmware_looks_for(hass):
    """Home Assistant may put the name of the device before the id of a new entity: the reader must still find it."""
    from homeassistant.helpers import entity_registry as er

    entry = await _house(hass)
    registry = er.async_get(hass)
    registry.async_update_entity("sensor.vigil_tag_garage_state", new_entity_id="sensor.garage_reader_vigil_tag_garage_state")
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.vigil_tag_garage_state") is not None
    assert hass.states.get("sensor.garage_reader_vigil_tag_garage_state") is None


async def test_the_panel_shows_the_esphome_devices_to_pick_from(hass, hass_ws_client):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    MockConfigEntry(domain="esphome", title="Vigil tag garage", data={"device_name": "vigil-tag-garage", "host": "x"}).add_to_hass(hass)
    MockConfigEntry(domain="esphome", title="Another", data={"device_name": "another-one", "host": "y"}).add_to_hass(hass)
    await _house(hass)
    client = await hass_ws_client(hass)
    got = (await _ws(client, type="vigil_alarm/get"))["result"]
    assert got["esphome_devices"] == [{"name": "another-one", "title": "Another"},
                                      {"name": "vigil-tag-garage", "title": "Vigil tag garage"}]


async def test_the_state_sensor_of_a_reader_tells_how_many_seconds_of_the_delay_are_left(hass):
    await _setup(hass, make_entry(extra_subentries=[
        panel_item("vigil-tag-door", "Door reader", "r_door", None, device_kind="tagreader", reader_mode="away",
                   reader_disarm=True), TESS]))
    assert hass.states.get("sensor.vigil_tag_door_state").attributes["delay_left"] is None
    await _scan(hass, "04-A1-B2-C3", reader="vigil-tag-door")
    state = hass.states.get("sensor.vigil_tag_door_state")
    assert state.state == "arming" and 0 < state.attributes["delay_left"] <= 60


async def test_a_reader_without_entities_is_reachable_when_esphome_says_it_is_connected(hass):
    from types import SimpleNamespace

    from pytest_homeassistant_custom_component.common import MockConfigEntry

    esp = MockConfigEntry(domain="esphome", title="Vigil tag garage", data={"device_name": "vigil-tag-garage", "host": "x"})
    esp.add_to_hass(hass)
    await _house(hass)
    panels = _manager(hass).panels
    esp.runtime_data = SimpleNamespace(available=True)
    assert panels._connected("vigil-tag-garage") is True
    esp.runtime_data = SimpleNamespace(available=False)
    assert panels._connected("vigil-tag-garage") is False


async def test_a_reader_with_a_key_must_send_it(hass):
    await _house(hass)
    panels = _manager(hass).panels
    key = panels.create_key(panels.for_reader("vigil-tag-garage"))
    await _scan_with_key(hass, "04-A1-B2-C3", None)  # no key
    assert hass.states.get(PANEL).state == "disarmed"
    assert hass.states.get(EVENTS).attributes["event_type"] == "panel_refused"
    assert hass.states.get(EVENTS).attributes["reason"] == "key"
    await _scan_with_key(hass, "04-A1-B2-C3", "not-the-key")
    assert hass.states.get(PANEL).state == "disarmed"
    await _scan_with_key(hass, "04-A1-B2-C3", key)
    assert hass.states.get(PANEL).state == "armed_home"


async def test_a_reader_without_a_key_works_as_before_but_is_pointed_out(hass):
    await _house(hass)
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "armed_home"
    assert {"code": "panel_no_key", "name": "Garage reader"} in _manager(hass).panels.problems()
    panels = _manager(hass).panels
    panels.create_key(panels.for_reader("vigil-tag-garage"))
    assert {"code": "panel_no_key", "name": "Garage reader"} not in panels.problems()
    assert not any(p["code"] == "panel_firmware" for p in panels.problems())  # a reader has no profile to understand


async def _scan_with_key(hass, tag, key, reader="vigil-tag-garage"):
    data = {"reader": reader, "tag": tag}
    if key is not None:
        data["key"] = key
    hass.bus.async_fire(READER_EVENT, data)
    await hass.async_block_till_done()


async def test_a_refused_scan_raises_the_counter_the_reader_shows(hass):
    await _house(hass)
    sensor = "sensor.vigil_tag_garage_state"
    assert hass.states.get(sensor).attributes["refused"] == 0
    await _scan(hass, "FF-FF-FF-FF")  # unknown tag
    assert hass.states.get(sensor).attributes["refused"] == 1
    await _scan_with_key(hass, "04-A1-B2-C3", None)  # a good tag, no key needed yet: not refused
    assert hass.states.get(sensor).attributes["refused"] == 1


async def test_a_wrong_key_and_a_disarm_that_is_not_allowed_count_as_refused(hass):
    await _house(hass)
    panels = _manager(hass).panels
    key = panels.create_key(panels.for_reader("vigil-tag-garage"))
    await _scan_with_key(hass, "04-A1-B2-C3", "wrong")
    assert hass.states.get("sensor.vigil_tag_garage_state").attributes["refused"] == 1
    assert _manager(hass).tags.refused["vigil-tag-garage"] == 1
    await _scan_with_key(hass, "04-A1-B2-C3", key)
    assert _manager(hass).tags.refused["vigil-tag-garage"] == 1


async def test_a_reader_that_reports_nothing_is_old_firmware(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    await _house(hass)
    esp = MockConfigEntry(domain="esphome", title="Vigil tag garage", data={"device_name": "vigil-tag-garage", "host": "x", "port": 6053})
    esp.add_to_hass(hass)
    esp.runtime_data = type("RD", (), {"available": True})()
    panels = _manager(hass).panels
    assert any(p["code"] == "panel_firmware" and p["seen"] == "?" for p in panels.problems())
    status = next(r for r in panels.status() if r["panel_id"] == "vigil-tag-garage")
    assert status["profile_required"] == 1 and status["reported"] == {}


async def test_a_held_tag_does_not_push_the_pause_away(hass):
    """The 3 seconds count from the scan that did something, not from the last one that was ignored."""
    await _house(hass)
    manager = _manager(hass)
    clock = {"t": 1000.0}
    manager._wall = lambda: clock["t"]
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "armed_home"
    for step in (1.0, 2.0, 2.9):  # held: ignored
        clock["t"] = 1000.0 + step
        await _scan(hass, "04-A1-B2-C3")
        assert hass.states.get(PANEL).state == "armed_home"
    clock["t"] = 1003.1  # more than 3 seconds after the scan that counted
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "disarmed"


async def test_a_reader_that_may_not_disarm_can_still_cancel_the_exit_delay(hass):
    data = {"device_kind": "tagreader", "reader_mode": "home", "reader_disarm": False}
    await _setup(hass, make_entry(extra_subentries=[panel_item("vigil-tag-garage", "Garage reader", "r_garage", None, **data),
                                                    TESS, BOB], exit_delay_home=30))
    manager = _manager(hass)
    clock = {"t": 1000.0}
    manager._wall = lambda: clock["t"]
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "arming"
    clock["t"] += 5
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "disarmed"  # cancelled: the exit delay was still running
    clock["t"] += 5
    await _scan(hass, "04-A1-B2-C3")
    assert hass.states.get(PANEL).state == "arming"  # armed again


async def test_unknown_tags_can_be_linked_by_an_administrator(hass, hass_ws_client):
    await _house(hass)
    await _scan(hass, "FF-EE-DD-CC")
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "vigil_alarm/unknown_tags"})
    res = (await client.receive_json())["result"]
    assert [t["tag"] for t in res["tags"]] == ["FF-EE-DD-CC"] and res["tags"][0]["reader"] == "Garage reader"
    # the number is in no event of the log
    assert "FF-EE-DD-CC" not in str(hass.states.get(EVENTS).attributes)
