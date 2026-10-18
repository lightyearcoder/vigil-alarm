"""Release 0.5.3: alarm memory with the path, cancel window, duress code and chime."""

from __future__ import annotations

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.vigil_alarm.credentials import hash_code

from .common import PANEL, make_entry, sub, user_data
from .test_integration import _call, _setup, _tick
from .test_notifications import channel
from .test_panel import _client, _ws


def _kinds(manager):
    return [e["event"] for e in manager.eventlog.entries]


async def _alarm_in_the_house(hass, freezer, **data):
    """Armed at home, the front door opens, the entry delay runs out: an intrusion alarm."""
    entry = await _setup(hass, make_entry(**data))
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    assert manager.engine.state == "triggered"
    return entry, manager


# ------------------------------------------------------------ alarm memory


async def test_the_memory_keeps_every_sensor_that_opens_during_the_alarm(hass, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer)
    # The living PIR is only active in "away": at home it does not count, but it tells where someone walked.
    hass.states.async_set("binary_sensor.living_pir", "on")
    await hass.async_block_till_done()
    memory = manager.alarmmemory
    assert memory.recording
    names = [(s["name"], s["counted"]) for s in memory.view()["path"]]
    assert names == [("Front door", True), ("Living PIR", False)]
    assert "alarm_sensor_seen" in _kinds(manager)  # the sensor that did not count has its own line in the log
    assert _kinds(manager).count("sensor_faulted") == 1  # the one that counted is not written twice

    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    view = memory.view()
    assert not view["recording"] and view["ended_by"].startswith("Anna") and len(view["path"]) == 2
    assert view["sensor_name"] == "Front door" and view["cause"] == "intrusion"


async def test_a_flickering_sensor_is_one_step_with_a_count(hass, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer)
    for state in ("on", "off", "on", "off", "on"):
        hass.states.async_set("binary_sensor.living_pir", state)
        await hass.async_block_till_done()
    steps = [s for s in manager.alarmmemory.view()["path"] if s["sensor"] == "living"]
    assert len(steps) == 1 and steps[0]["n"] == 3


async def test_an_entry_delay_that_ends_in_a_disarm_leaves_no_memory(hass, freezer):
    entry = await _setup(hass, make_entry())
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    assert manager.engine.state == "pending"
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert manager.alarmmemory.view() is None
    assert hass.states.get(PANEL).attributes["last_alarm"] is None


async def test_the_memory_is_in_the_attributes_survives_a_restart_and_is_cleared_without_a_code(hass, hass_ws_client, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer)
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    last = hass.states.get(PANEL).attributes["last_alarm"]
    assert last["sensor"] == "Front door" and last["path"] == ["Front door"] and last["steps"] == 1

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    manager = entry.runtime_data
    assert manager.alarmmemory.view()["sensor_name"] == "Front door"  # kept over a restart

    client = await hass_ws_client(hass)
    from custom_components.vigil_alarm.panel import _live
    assert _live(entry)["alarm_memory"]["steps"] == 1
    res = await _ws(client, type="vigil_alarm/alarm_memory_clear")
    assert res["success"]
    assert manager.alarmmemory.view() is None and "alarm_memory_cleared" in _kinds(manager)


async def test_the_memory_is_not_cleared_while_the_alarm_still_runs(hass, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer)
    await manager.async_clear_alarm_memory()
    assert manager.alarmmemory.view() is not None


async def test_the_path_names_the_room_of_each_sensor(hass, freezer):
    area = ar.async_get(hass).async_create("Hall")
    registry = er.async_get(hass)
    reg = registry.async_get_or_create("binary_sensor", "test", "hd", suggested_object_id="hall_door")
    registry.async_update_entity(reg.entity_id, area_id=area.id)
    assert reg.entity_id == "binary_sensor.hall_door"
    hass.states.async_set("binary_sensor.hall_door", "off")
    entry = await _setup(hass, make_entry(extra_subentries=[
        sub("zone", "Hall door", {"entity_id": "binary_sensor.hall_door", "cls": "intrusion", "type": "delayed",
                                  "sensor_groups": ["g_all"]}, "hall")]))
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.hall_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    assert manager.alarmmemory.view()["path"][0]["area"] == "Hall"
    assert hass.states.get(PANEL).attributes["last_alarm"]["path"] == ["Hall door (Hall)"]


# ------------------------------------------------------------ cancel window


async def test_a_code_soon_after_the_siren_makes_it_a_false_alarm(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    entry, manager = await _alarm_in_the_house(hass, freezer, trigger_time=0)
    await _tick(hass, freezer, 20)
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "alarm_cancelled" in _kinds(manager)
    assert manager.alarmmemory.view()["cancelled"] is True
    assert hass.states.get(PANEL).attributes["last_alarm"]["cancelled"] is True


async def test_the_false_alarm_message_goes_to_the_channels(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    entry = await _setup(hass, make_entry(extra_subentries=[channel()]))
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "Alarm cancelled: false alarm by Anna" in [c.data["message"] for c in calls]


async def test_after_the_window_a_disarm_is_just_a_disarm(hass, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer)
    await _tick(hass, freezer, 61)
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "alarm_cancelled" not in _kinds(manager)
    assert manager.alarmmemory.view()["cancelled"] is False


async def test_a_window_of_zero_switches_the_cancel_off(hass, freezer):
    entry, manager = await _alarm_in_the_house(hass, freezer, abort_seconds=0)
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "alarm_cancelled" not in _kinds(manager)


async def test_a_fire_alarm_is_never_called_a_false_alarm(hass, freezer):
    entry = await _setup(hass, make_entry())
    manager = entry.runtime_data
    hass.states.async_set("binary_sensor.smoke", "on")
    await hass.async_block_till_done()
    assert manager.engine.state == "triggered" and manager.engine.cause == "fire"
    await _call(hass, "alarm_disarm", code="1234")
    await hass.async_block_till_done()
    assert "alarm_cancelled" not in _kinds(manager)


# ------------------------------------------------------------- duress code


def _duress_house(**data):
    anna = user_data("1234", allowed_modes=[])
    anna["duress_hash"], anna["duress_salt"] = hash_code("9999")
    entry = make_entry(extra_subentries=[], **data)
    entry.options["items"]["anna"]["data"] = anna
    return entry


async def test_the_duress_code_disarms_quietly_and_warns_the_duress_channels(hass, freezer):
    calls = async_mock_service(hass, "notify", "mobile_app_anna")
    entry = _duress_house()
    entry.options["items"]["n1"] = {"type": "notification", "title": "Phone", "data": {
        "service": "mobile_app_anna", "categories": ["duress"], "delay": 0, "priority": True}}
    entry = await _setup(hass, entry)
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    await hass.async_block_till_done()
    last_before = manager.last_event
    await _call(hass, "alarm_disarm", code="9999")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"  # it works like the normal code
    assert [c.data["message"] for c in calls] == ["SILENT ALARM: Anna used the duress code at -"]
    assert calls[0].data["data"]["priority"] == "high"
    assert "duress_used" in _kinds(manager)
    assert manager.last_event["type"] == "disarmed"  # nothing on a dashboard shows it
    assert last_before is not None


async def test_the_duress_code_never_cancels_an_alarm(hass, freezer):
    entry = await _setup(hass, _duress_house())
    manager = entry.runtime_data
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.front_door", "on")
    await hass.async_block_till_done()
    await _tick(hass, freezer, 31)
    await _call(hass, "alarm_disarm", code="9999")
    await hass.async_block_till_done()
    kinds = _kinds(manager)
    assert "disarmed" in kinds and "duress_used" in kinds and "alarm_cancelled" not in kinds


async def test_a_duress_code_needs_a_code_a_channel_and_must_be_unique(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    user = {"name": "Carl", "code": "4321", "duress_code": "8888", "tags": [], "allowed_modes": []}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data=user)
    assert res["result"]["errors"] == {"duress_code": "duress_no_channel"}

    channel_data = {"name": "Duress phone", "service": "mobile_app_anna", "categories": ["duress"], "delay": 0}
    async_mock_service(hass, "notify", "mobile_app_anna")
    res = await _ws(client, type="vigil_alarm/save", kind="notification", data=channel_data)
    assert res["result"]["ok"]
    await hass.async_block_till_done()

    res = await _ws(client, type="vigil_alarm/save", kind="user", data={**user, "duress_code": "1234"})  # Anna's code
    assert res["result"]["errors"] == {"duress_code": "code_in_use"}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={**user, "duress_code": "4321"})  # his own code
    assert res["result"]["errors"] == {"duress_code": "code_in_use"}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={**user, "code": "", "duress_code": "8888", "tags": ["t1"]})
    assert res["result"]["errors"] == {"duress_code": "duress_needs_code"}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data=user)
    assert res["result"]["ok"]
    await hass.async_block_till_done()

    snapshot = (await _ws(client, type="vigil_alarm/get"))["result"]
    carl = next(u for u in snapshot["items"]["user"] if u["title"] == "Carl")
    assert carl["has_duress"] is True and "duress_hash" not in carl["data"] and "duress_salt" not in carl["data"]

    # Another user may not choose Carl's duress code as an ordinary code either.
    res = await _ws(client, type="vigil_alarm/save", kind="user", data={"name": "Dora", "code": "8888", "tags": [], "allowed_modes": []})
    assert res["result"]["errors"] == {"code": "code_in_use"}


async def test_editing_a_user_keeps_the_duress_code_unless_it_is_removed(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    async_mock_service(hass, "notify", "mobile_app_anna")
    await _ws(client, type="vigil_alarm/save", kind="notification",
              data={"name": "Duress phone", "service": "mobile_app_anna", "categories": ["duress"], "delay": 0})
    user = {"name": "Carl", "code": "4321", "duress_code": "8888", "tags": [], "allowed_modes": []}
    res = await _ws(client, type="vigil_alarm/save", kind="user", data=user)
    uid = res["result"]["id"]
    await hass.async_block_till_done()
    res = await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=uid,
                    data={"name": "Carl", "tags": [], "allowed_modes": []})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert entry.options["items"][uid]["data"].get("duress_hash")
    res = await _ws(client, type="vigil_alarm/save", kind="user", subentry_id=uid,
                    data={"name": "Carl", "tags": [], "allowed_modes": [], "remove_duress": True})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert not entry.options["items"][uid]["data"].get("duress_hash")


# ------------------------------------------------------------------- chime


def _chime_house(**data):
    entry = make_entry(extra_subentries=[
        sub("zone", "Back door", {"entity_id": "binary_sensor.back_door", "cls": "intrusion", "type": "delayed",
                                  "sensor_groups": ["g_all"], "chime": True}, "back"),
    ], **data)
    return entry


async def test_the_chime_sounds_when_a_door_opens_while_the_alarm_is_off(hass):
    hass.states.async_set("binary_sensor.back_door", "off")
    entry = await _setup(hass, _chime_house(chime_entity="switch.bell"))
    calls = async_mock_service(hass, "switch", "turn_on")  # after the set-up: the switch platform registers its own
    manager = entry.runtime_data
    seen = []
    from custom_components.vigil_alarm.manager import SIGNAL_EVENT
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    async_dispatcher_connect(hass, SIGNAL_EVENT.format(entry.entry_id), lambda e: seen.append(e["type"]))
    hass.states.async_set("binary_sensor.back_door", "on")
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in calls] == ["switch.bell"]
    assert "chime" in seen and "chime" not in _kinds(manager)  # on the event entity, not in the log
    assert manager.last_event is None or manager.last_event["type"] != "chime"


async def test_no_chime_when_armed_or_for_a_sensor_without_it(hass):
    hass.states.async_set("binary_sensor.back_door", "off")
    entry = await _setup(hass, _chime_house(chime_entity="switch.bell"))
    calls = async_mock_service(hass, "switch", "turn_on")
    hass.states.async_set("binary_sensor.front_door", "on")  # no chime on this one
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.front_door", "off")
    await _call(hass, "alarm_arm_home", code="1234")
    hass.states.async_set("binary_sensor.back_door", "on")
    await hass.async_block_till_done()
    assert calls == []


async def test_a_door_that_flickers_chimes_once(hass):
    hass.states.async_set("binary_sensor.back_door", "off")
    await _setup(hass, _chime_house(chime_entity="switch.bell"))
    calls = async_mock_service(hass, "switch", "turn_on")
    for state in ("on", "off", "on", "off", "on"):
        hass.states.async_set("binary_sensor.back_door", state)
        await hass.async_block_till_done()
    assert len(calls) == 1


async def test_the_chime_flag_is_only_for_intrusion_sensors(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/save", kind="sensor", data={
        "name": "Smoke 2", "entity_id": "binary_sensor.smoke2", "cls": "fire", "chime": True})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert "chime" not in next(s for s in entry.options["items"].values() if s["title"] == "Smoke 2")["data"]


async def test_the_settings_accept_the_cancel_window_and_the_chime(hass, hass_ws_client):
    entry, client = await _client(hass, hass_ws_client)
    snapshot = (await _ws(client, type="vigil_alarm/get"))["result"]
    data = dict(snapshot["entry"]["data"])
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "abort_seconds": 601})
    assert res["result"]["errors"] == {"abort_seconds": "seconds_range"}
    res = await _ws(client, type="vigil_alarm/save_settings", data={**data, "chime_entity": "light.hall", "chime_seconds": 5, "abort_seconds": 45})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert entry.data["abort_seconds"] == 45 and entry.data["chime_entity"] == "light.hall"
    res = await _ws(client, type="vigil_alarm/save_settings", data={**entry.data, "chime_entity": "sensor.nope"})
    assert res["result"]["errors"] == {"chime_entity": "chime_entity_domain"}
    res = await _ws(client, type="vigil_alarm/save_settings", data={**entry.data, "chime_entity": ""})
    assert res["result"]["ok"]
    await hass.async_block_till_done()
    assert "chime_entity" not in entry.data
